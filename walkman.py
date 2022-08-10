#!/usr/bin/python3
# 
#  This is a script that you run to pull playlists from Plex
#  After running it, you can add your music files to the music player, very old skool

from plexapi.myplex import MyPlexAccount
from pathlib import Path
import yaml
from plexapi.server import PlexServer
import os

configfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.yaml')
with open(configfile) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
baseurl=config['server']
token=config['token']
plex = PlexServer(baseurl, token)


# download playlist tracks to current folder. 

for playlist in plex.playlists(playlistType='audio'): #only output audio playlists
    tracks = playlist.items()
    for track in range(len(tracks)): #loop over tracks
        p = Path(tracks[track].locations[0]) #get the path
        path = Path("music/"+playlist.title+"/"+p.name)                                      # It will save each playlist in its own folder
        if path.is_file(): #skips files that already exist
            print(f'File {path} exists - skipping')
        else:
            print(f'Creating {path}')
            tracks[track].download(keep_original_name=True,savepath=playlist.title) 
