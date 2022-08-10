#!/usr/bin/python3
# 
#  This is a script that you run to pull playlists from Plex
#  After running it, you can add your music files to the music player, very old skool

from plexapi.myplex import MyPlexAccount
from pathlib import Path
import yaml
from plexapi.server import PlexServer
import os

dirname = os.path.dirname(__file__)
musicdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'music')
configfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.yaml')
with open(configfile) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
baseurl=config['server']
token=config['token']
pathprefix=config['pathprefix']
plex = PlexServer(baseurl, token)

# download playlist tracks to current folder. 

for playlist in plex.playlists(playlistType='audio'): #only output audio playlists
    index=1
    tracks = playlist.items()
    playlist_title=playlist.title
    print(' Playlist generation done')
    filename = os.path.join(os.path.join(musicdir,playlist_title),playlist_title+'.pls')
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    pls =open( filename, 'w')
    for track in range(len(tracks)): #loop over tracks
        media = tracks[track].media[0]
        seconds = int(tracks[track].duration / 1000)
        title = tracks[track].title        
        album = tracks[track].parentTitle
        artist = tracks[track].originalTitle
        albumArtist = tracks[track].grandparentTitle
        if artist == None:
            artist = albumArtist        
        p = Path(tracks[track].locations[0]) #get the path
        fullpathoftrack=pathprefix+playlist.title+"/"+p.name
        pathoftrack=playlist.title+"/"+p.name
        pls.write(fullpathoftrack+'\r\n')
        path = Path("music/"+pathoftrack)                                      # It will save each playlist in its own folder
        if path.is_file(): #skips files that already exist
            print(f'File {path} exists - skipping')
        else:
            print(f'Creating {path}')
            tracks[track].download(keep_original_name=True,savepath="music/"+playlist_title)
        index=index+1
    pls.close()
