#!/usr/bin/python3
#  This is a script that you run to pull playlists from Plex
#  After running it, you can add your music files to the music player
#  or if it is connected, it will rsync to the player

import os
import re
import getpass
import subprocess
import shutil
import argparse
from pathlib import Path

import yaml
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import Unauthorized, TwoFactorRequired

# Characters that are illegal in Windows/exFAT/FAT32 paths.
# Used to sanitize album/track names before using them as folder/file names.
ILLEGAL_PATH_CHARS = re.compile(r'[\\/:*?"<>|]')


def ignorestringtolist(astring):
    # Takes the string for currencies in the config.yaml
    # file and turns it into a list
    curr_list = astring.split(",")
    curr_list = [x.strip(' ') for x in curr_list]
    return curr_list


def sanitize(name):
    # Strip characters that aren't safe in folder/file names
    # (FIX: album/track titles can contain ':', '/', etc., which
    # break os.path.join and many filesystems otherwise)
    return ILLEGAL_PATH_CHARS.sub('_', name).strip()


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--purge", action='store_true', help="Refresh local copy of files")
args = parser.parse_args()

# run with -p flag to purge the local library.
if args.purge is True:
    print('Clearing ./music... This slows things down, but makes things cleaner')
    shutil.rmtree("music", ignore_errors=True)

dirname = os.path.dirname(os.path.realpath(__file__))
musicdir = os.path.join(dirname, 'music')
configfile = os.path.join(dirname, 'config.yaml')

with open(configfile) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

baseurl = config['server']
pathprefix = config['devicepathprefix']
ignorelist = ignorestringtolist(config['ignorestring'])


def login_with_credentials(config):
    # Prompts for username/password (and 2FA code if needed), then
    # returns a logged-in MyPlexAccount.
    username = config.get('username') or input("Plex username/email: ")
    password = config.get('password') or getpass.getpass("Plex password: ")
    try:
        return MyPlexAccount(username, password)
    except TwoFactorRequired:
        # FIX: confirmed via docs, TwoFactorRequired is a subclass of
        # Unauthorized that's raised specifically when 2FA is needed
        # but no code was supplied.
        code = input("2FA code: ").strip()
        return MyPlexAccount(username, password, code=code)


# NOTE: per python-plexapi docs, MyPlexAccount(token=...) is a documented
# alternative to username/password. We try the saved token first (if any)
# and only fall back to prompting for credentials if it's missing or
# rejected by the server.
token = config.get('token')
account = None

if token:
    try:
        candidate = MyPlexAccount(token=token)
        # Touching `resources()` forces an authenticated call to plex.tv,
        # which will raise Unauthorized if the token is invalid/expired.
        candidate.resources()
        account = candidate
        print('Logged in with saved token')
    except Unauthorized:
        print('Saved token is invalid or expired, falling back to login')

if account is None:
    account = login_with_credentials(config)
    # Save the new token back to config.yaml so future runs don't need
    # to prompt for credentials again.
    # NOTE: this rewrites config.yaml via yaml.dump, which will strip
    # any comments you have in the file. If that matters to you, let me
    # know and I can write the token to a separate file instead.
    config['token'] = account.authenticationToken
    with open(configfile, 'w') as f:
        yaml.dump(config, f)
    print('Saved new token to config.yaml')

plex = account.resource(baseurl).connect()  # returns a PlexServer instance
print('Connected to Plex')

# download playlist tracks to current folder.
# remove any from the list below if you'd like to import them.
ignoredlists = ignorelist + \
    ['All Music',
     'Recently Added',
     'Recently Played',
     'Fresh ❤️',
     '❤️ Tracks']

# Audio Playlists Only
for playlist in plex.playlists(playlistType='audio'):
    if playlist.title in ignoredlists:
        print('Skipping Playlist: ', playlist.title)
        continue

    print('Processing: ', playlist.title)
    tracks = playlist.items()

    filenamem3u = os.path.join('music', playlist.title + '.m3u')
    m3u_dir = os.path.dirname(filenamem3u)
    if not os.path.exists(m3u_dir):
        os.makedirs(m3u_dir)

    # FIX: use a context manager so the file is always closed/flushed,
    # even if something raises partway through the loop.
    with open(filenamem3u, 'w') as m3u:
        m3u.write('#EXTM3U\r\n')
        m3u.write('#PLAYLIST:%s\r\n' % playlist.title)
        m3u.write('\r\n')

        for track in tracks:  # FIX: iterate directly instead of range(len(...))
            album = sanitize(track.parentTitle)
            artist = track.originalTitle
            albumArtist = track.grandparentTitle
            if artist is None:
                artist = albumArtist

            # `locations` is a synthetic plexapi convenience property:
            # one file path per "part" of the track (almost always 1,
            # but can be more for multi-part tracks).
            locations = track.locations

            # FIX: write one m3u entry per actual file/part, instead of
            # writing the same entry multiple times for multi-part tracks.
            for loc in locations:
                p = Path(loc)
                breadcrumbm3u = "\\".join([album, p.name])
                m3u.write('#EXTINF:\r\n')
                m3u.write('\\Music\\%s\r\n' % breadcrumbm3u)
                m3u.write('\r\n')

            pathstr = os.path.join("music", album)

            # Check existence using the expected local filenames before downloading,
            # so we don't re-download tracks we already have.
            expected_paths = [
                Path(os.path.normpath(os.path.join(pathstr, Path(loc).name)))
                for loc in locations
            ]

            if expected_paths and all(p.is_file() for p in expected_paths):
                print(f'File(s) for "{track.title}" already exist - skipping')
            else:
                print(f'Downloading: {track.title}')
                # FIX: use the list of filepaths download() actually returns,
                # instead of re-deriving/guessing the path ourselves.
                saved_paths = track.download(
                    keep_original_name=True, savepath=pathstr)
                for sp in saved_paths:
                    print(f'  Saved: {sp}')

print('Attempting rsync on ./music and', pathprefix)
path = os.path.join('/', pathprefix)
pluggedin = Path(path).is_dir()

if pluggedin:
    # FIX: --exclude was previously a malformed standalone string
    # ("exclude='.*'") which rsync would treat as an extra source path,
    # not as an exclude option. This is the correct syntax.
    subprocess.call(
        ["rsync", "-avh", "--delete", "--size-only",
         "--exclude=.*", "--ignore-errors",
         "music/", pathprefix]
    )
else:
    print('Check Player is Mounted at:', pathprefix)
    print('Copies of music are in the directory ./music')
