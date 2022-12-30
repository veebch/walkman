[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

# Walkman

Get copies of audio files from Plex playlists to add to a DAC walkman. This is very bare bones and assumes that you keep a relatively small playlist for use on your DAC.

# Dependencies

Uses `plexapi` module. Install it with the command:

    python3 -m pip install plexapi

# Installation 

    git clone https://github.com/veebch/walkman
    cd walkman
    cp config_example.yaml config.yaml
    
Then edit the config.yaml file with your own credentials and the mount point of your music player.

# Run 

`python3 walkman.py`

The files that make up the playlists should now each be in a separate directory in the folder `music`, ready to be dragged to your music player. If your player is mounted and configured correctly it will rsync with that directory.

