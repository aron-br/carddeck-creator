#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__      = 'Aron Brüggmann'
__copyright__   = 'Copyright 2023, Aron Brüggmann'

'''
main.py: Run this script to create an instance of SpotifyGateway and query metadata of a spotify playlist using the spotify API. Postprocess the playlist and save the original and processed datasets.  
'''

import os
from spotify_gateway import SpotifyGateway
from carddeck import CardDeck
from settings import *
from utils import *

# ------------------------- Filenames etc. -------------------------
# define a general filename for all generated files
filename = "./hitster_birthday_edition"

# define a name for the CSV file that will contain the playing cards
playlist_filename = filename + ".csv"

#  define a name for the HTML file that will contain the playing cards
html_filename = filename + ".html"

# define a name for the summary file that contains some key numbers and facts
summary_filename = filename + "_summary.pdf"

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
skip_postprocessing=False

# create a copy of the playlist dataset before modifying it
playlist = spotify_gateway.playlist.copy()

if not skip_postprocessing:
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
                                append_column='release_year_raw')

# preserve raw spotify release year before validation
playlist["release_year"] = playlist["release_year_raw"].copy()


playlist, change_log = validate_and_fix_release_years(
    playlist=playlist,
    spotify_gateway=spotify_gateway,
    overwrite=True
)

pd.DataFrame(change_log).to_csv(
    os.path.join(DATA_FOLDER, "year_changes.csv"),
    index=False
)

# add column with epoch to dataframe
playlist['epoch'] = [find_epoch(year=year) for year in playlist['release_year']]

# save datafame as csv
playlist.to_csv(os.path.join(DATA_FOLDER, playlist_filename), index=False)

if not skip_postprocessing:
    # get some stats about the dataframe
    summary = summarize_dataframe(df=playlist, export_pdf=True, pdf_filename=summary_filename)

    # print summary to console
    print("\nDATASET SUMMARY")
    print(f"Songs: {summary['songs']}")
    print(f"Artists: {summary['artists']}")
    print(f"Contributors: {summary['contributors']}")
    print(f"Oldest Release Year: {summary['oldest_release_year']}")
    print(f"Latest Release Year: {summary['latest_release_year']}")

# ------------------------- CREATION OF CARD DECK -------------------------
# specify path to the jinja template
card_template = os.path.join(os.getcwd(), 'src/carddeck_creator/static/templates/card_template_A4.jinja')

# specify the name of customizable fields in the template
template_fields=  ['text1', 'text2', 'text3', 'smallText', 'number', 'backImage']

# which column should be used to fill the template fields !ORDER MATTERS!
# content_columns[0] is written in field with name template_field[0]
# content_columns[1] is written in field with name template_field[1], etc.
content_columns= ['song', 'release_year', 'artist', 'contributor_name', 'number', 'code_file']

# define the batch size (how many cards fit on one page of template)
batch_size = 9

# create a CardDeck instance
card_deck = CardDeck(data=playlist,
                    content_columns=content_columns,
                    card_template=card_template,
                    batch_size=batch_size,
                    template_fields=template_fields)

# create a printable html file that contains the custom playing cards
card_deck.create_cards(filename=html_filename)