[![YouTube Channel Views](https://img.shields.io/youtube/channel/views/UCz5BOU9J9pB_O0B8-rDjCWQ?label=YouTube&style=social)](https://www.youtube.com/channel/UCz5BOU9J9pB_O0B8-rDjCWQ)

# Walkman

A few lines of Python to get copies of audio files from Plex playlists to add to a walkman.

# Dependencies

Uses `plexapi` module

# Installation 

    git clone https://github.com/veebch/walkman
    cd walkman

[Add your plex token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) to the file `walkman.py` (and adjust the hostname if needed).

# Run 

`python3 walkman.py`

The files that make up the playlists should now each be in a separate directory.

# Alternative

For something more robust with more features, use [PPP](https://github.com/XDGFX/PPP)
