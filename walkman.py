#!/usr/bin/python3
# 
#  This is a script that you run to pull playlists from Plex
#  After running it, you can add your music files to the music player, very old skool

from plexapi.myplex import MyPlexAccount
from pathlib import Path

from plexapi.server import PlexServer
baseurl = 'http://127.0.0.1:32400/' # Or URL of Plex Server if it's not running on local machine
token = '<INSERT PLEX TOKEN>'
plex = PlexServer(baseurl, token)


# download playlist tracks to current folder. 

for playlist in plex.playlists(playlistType='audio'): #only output audio playlists
    tracks = playlist.items()
    for track in range(len(tracks)): #loop over tracks
        p = Path(tracks[track].locations[0]) #get the path
        path = Path(playlist.title+"/"+p.name)                                      # It will save each playlist in its own folder
        if path.is_file(): #skips files that already exist
            print(f'File {path} exists - skipping')
        else:
            print(f'Creating {path}')
            tracks[track].download(keep_original_name=True,savepath=playlist.title) 
