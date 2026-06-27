#!/usr/bin/python3
#  This is a script that you run to pull playlists from Plex
#  After running it, you can add your music files to the music player
#  or if it is connected, it will rsync to the player

import os
import re
import subprocess
import shutil
import argparse
from pathlib import Path

import yaml
from plexapi.myplex import MyPlexAccount

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
password = config['password']
username = config['username']
pathprefix = config['devicepathprefix']
ignorelist = ignorestringtolist(config['ignorestring'])

# NOTE: per python-plexapi docs, this expects your Plex SERVER NAME
# (as shown in Plex Web), not a hostname/URL. If `server:` in your
# config.yaml is a URL, double check this is actually working as
# intended rather than relying on some other fallback behavior.
account = MyPlexAccount(username, password)
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
