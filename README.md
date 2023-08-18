[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

# Walk, Man

Download the *original resolution* audio files from Plex playlists and add to a portable music player (DAP).

# Features

- Uses rsync to mirror local copy to the device

# Dependencies

Install the required Python3 modules

    python3 -m pip install -r requirements.txt

# Installation 

    git clone https://github.com/veebch/walkman
    cd walkman
    cp config_example.yaml config.yaml
    
Then edit the config.yaml file with your own Plex.tv credentials, server name, and the mount point of your music player, along with any playlist(s) that you want to ignore.

# Run 

`python3 walkman.py`

If you want to have a clear out of the local intermediate files, just run it with the flag to purge the local copy of the playlist:

`python3 walkman.py -p`

The files that make up the playlists should now each be in a separate directory in the folder `music`, ready to be dragged to your music player. If your player is mounted and configured correctly it will also rsync with that directory.

