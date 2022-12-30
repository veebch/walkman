#!/usr/bin/python3
# 
#  This is a script that you run to pull playlists from Plex
#  After running it, you can add your music files to the music player, very old skool

from plexapi.myplex import MyPlexAccount
from pathlib import Path
import yaml
from plexapi.server import PlexServer
import os
import subprocess
from pathlib import Path

print('Clearing Music Directory')
os.system("rm -r ./music")
dirname = os.path.dirname(__file__)
musicdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'music')
configfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.yaml')
with open(configfile) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
baseurl = config['server']
password = config['password']
username =config['username']
pathprefix = config['devicepathprefix']
playerpathprefix = "/Music/"
account = MyPlexAccount(username, password)
plex = account.resource(baseurl).connect()  # returns a PlexServer instance
print('Connected to Plex')
# download playlist tracks to current folder. 
ignoredlists = ['All Music','Recently Added', 'Recently Played','Fresh ❤️', '❤️ Tracks']
for playlist in plex.playlists(playlistType='audio'): #only output audio playlists
    playlist_title = playlist.title
    if playlist_title in ignoredlists:
        print ('Skipping Playlist: ', playlist_title)
    else:
        print('Processing: ',playlist_title)
        tracks = playlist.items()
        filenamem3u = os.path.join(os.path.join(musicdir,playlist_title),playlist_title+'.m3u')
        dirname = os.path.dirname(filenamem3u)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        m3u = open(filenamem3u, 'w')
        m3u.write('#EXTM3U\r\n')
        m3u.write('#PLAYLIST:%s\r\n' % playlist_title)
        m3u.write('\r\n')
        for track in range(len(tracks)): #loop over tracks
            media = tracks[track].media[0]
            seconds = int(tracks[track].duration / 1000)
            title = tracks[track].title        
            print ('Title: ', title)
            album = tracks[track].parentTitle
            artist = tracks[track].originalTitle
            albumArtist = tracks[track].grandparentTitle
            if artist == None:
                artist = albumArtist        
            p = Path(tracks[track].locations[0]) #get the path
            fullpathoftrack = playerpathprefix+playlist.title+"/"+p.name
            pathoftrack=playlist.title+"/"+p.name
            m3u.write('#EXTALB:%s\n' % album)
            m3u.write('#EXTART:%s\n' % albumArtist)
            parts = media.parts
            for part in parts:
                m3u.write('#EXTINF:%s,%s - %s\r\n' % (seconds, artist, title))
                m3u.write('\'%s\'\r\n' % fullpathoftrack)
                m3u.write('\r\n')
            path = Path("music/"+pathoftrack)                                      # It will save each playlist in its own folder
            if path.is_file(): #skips files that already exist
                print(f'File {path} exists - skipping')
            else:
                print(f'Creating {path}')
                tracks[track].download(keep_original_name=True,savepath="music/"+playlist_title)
        m3u.close()
print('Attempting rsync on ./music and', pathprefix)
path=os.path.join('/',pathprefix)
pluggedin = Path(path).is_dir()
if pluggedin:
    subprocess.call(["rsync", "-avv", "./music/", pathprefix])
else:
    print('Check the music player is connected and that the mount point is listed in config.yaml')
    print('Copies of music are in the directory ./music')

    
