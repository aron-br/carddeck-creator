#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__      = 'Aron Brüggmann'
__copyright__   = 'Copyright 2023, Aron Brüggmann'

'''
main.py: Run this script to create an instance of SpotifyGateway and query metadata of a spotify playlist using the spotify API. Postprocess the playlist and save the original and processed datasets.  
'''

import os
from spotify_gateway import SpotifyGateway
from settings import *
from utils import *

# ------------------------- SET UP PROJECT STRUCTURE !DO NOT MODIFY! -------------------------
# create project structure if it does not exist already
for folder in FOLDERS:
    if not os.path.exists(folder):
        os.mkdir(folder)

# ------------------------- CALL SPOTIFY API AND DOWNLOAD DATA !DO NOT MODIFY! -------------------------
# create an instance of a spotify gateway
spotify_gateway = SpotifyGateway(playlist_id=PLAYLIST_ID)

# call the API to download metadata
spotify_gateway.get_playlist_metadata()

# save playlist dataset to file
spotify_gateway.playlist.to_csv(os.path.join(DATA_FOLDER, 'playlist.csv'), index=False)

# ------------------------- POSTPROCESSING !CUSTOMIZE THIS TO YOUR NEEDS! -------------------------
# create a copy of the playlist dataset before modifying it
playlist = spotify_gateway.playlist.copy()

# modify the contributors of certain songs (ONLY NECESSARY IF ORIGINAL CONTRIBUTOR DIFFERS FROM CONTRIBUTOR DISPLAYED IN SPOTIFY)
playlist = modify_song_contributor_id(playlist=playlist,
                                      replace_dict=SONG_TO_CONTRIBUTOR,
                                      column='song',
                                      modify_column='contributor_id')

# add column with contributor names to dataframe
playlist = add_contributor_names(playlist=playlist,
                                 replace_dict=ID_TO_NAME,
                                 column='contributor_id',
                                 append_column='contributor_name')

# extract release year from release date strings
playlist = extract_release_year(playlist=playlist,
                                column='release_date',
                                append_column='release_year')

# modify release years (necessary for songs that are remastered -> I want the original release year)
playlist = modify_release_year(playlist=playlist,
                               replace_dict=SONG_TO_YEAR,
                               release_year_column='release_year',
                               song_column='song',
                               append_column='original_release_year')

# add column with epoch to dataframe
playlist['epoch'] = [find_epoch(year=year) for year in playlist['original_release_year']]

# save datafame as csv
playlist.to_csv(os.path.join(DATA_FOLDER, 'playlist_processed.csv'), index=False)

# get some stats about the dataframe
summary = summarize_dataframe(df=playlist)

# print summary to console
print(f"{summary['info']}\n{summary['number_of_songs_by_epoch']}\n{summary['number_of_songs_by_contributor']}")
