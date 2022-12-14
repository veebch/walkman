#!/usr/bin/python3


#  This is a script that you run to pull playlists from Plex
#  After running it, you can add your music files to the music player
#  or if it is connected, it will rync to the player

from plexapi.myplex import MyPlexAccount
from pathlib import Path
from plexapi.server import PlexServer
import os
import subprocess
import shutil
import yaml
import argparse


def ignorestringtolist(astring):
    # Takes the string for currencies in the config.yaml
    # file and turns it into a list
    curr_list = astring.split(",")
    curr_list = [x.strip(' ') for x in curr_list]
    return curr_list


parser = argparse.ArgumentParser()
parser.add_argument("-p","--purge", action='store_true', help="Refresh local copy of files")
args = parser.parse_args()
# run with -p flag to purge the local library. 
if args.purge is True:
    print('Clearing ./music... This slows things down, but makes things cleaner')
    shutil.rmtree("music", ignore_errors=True)

dirname = os.path.dirname(__file__)
musicdir = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)),
        'music')
configfile = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)),
        'config.yaml')
with open(configfile) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
baseurl = config['server']
password = config['password']
username = config['username']
pathprefix = config['devicepathprefix']
ignorelist = ignorestringtolist(config['ignorestring'])

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
    else:
        print('Processing: ', playlist.title)
        tracks = playlist.items()
        filenamem3u = os.path.join('music', playlist.title+'.m3u')
        dirname = os.path.dirname(filenamem3u)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        m3u = open(filenamem3u, 'w')
        m3u.write('#EXTM3U\r\n')
        m3u.write('#PLAYLIST:%s\r\n' % playlist.title)
        m3u.write('\r\n')
        for track in range(len(tracks)):            # loop over tracks
            media = tracks[track].media[0]
            # seconds = int(tracks[track].duration / 1000)
            # title = tracks[track].title
            album = tracks[track].parentTitle
            artist = tracks[track].originalTitle
            albumArtist = tracks[track].grandparentTitle
            if artist is None:
                artist = albumArtist
            p = Path(tracks[track].locations[0])    # get the path
            # m3u.write('#EXTALB:%s\n' % album)
            # m3u.write('#EXTART:%s\n' % albumArtist)
            tree = [album, p.name]
            delim = "\\"
            breadcrumbm3u = delim.join(tree)
            parts = media.parts
            for part in parts:
                m3u.write('#EXTINF:\r\n')
                muhstring = '\\Music\\' + breadcrumbm3u
                m3u.write('%s\r\n' % muhstring)
                m3u.write('\r\n')
            delim = "/"
            breadcrumb = delim.join(tree)
            pathstr = os.path.join("music", album)
            trackpath = Path(os.path.normpath("music/" + breadcrumb))
            if trackpath.is_file():                 # skips files that exist
                print(f'File {trackpath} exists - skipping')
            else:
                print(f'Creating {trackpath}')
                tracks[track].download(
                        keep_original_name=True, savepath=pathstr)
        m3u.close()


print('Attempting rsync on ./music and', pathprefix)
path = os.path.join('/', pathprefix)
pluggedin = Path(path).is_dir()
if pluggedin:
    subprocess.call(
            ["rsync", "-avh", "--delete", "--size-only", "music/",
             "exclude='.*'","--ignore-errors",
             pathprefix]
            )
else: 
    print('Check Player is Mounted at:', pathprefix)
    print('Copies of music are in the directory ./music')

