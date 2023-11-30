#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__      = "Aron Brüggmann"
__copyright__   = "Copyright 2023"

"""
utils.py: Some utility functions used in this project
"""

import pandas as pd
import urllib.request
from datetime import datetime


def __create_spotify_code_url(uri:str, code_color_as_text:str = 'black', background_color_as_hex:str = 'FFFFFF', format:str = 'png', size:int = 1024) -> str:
    '''Create a URL that can be used to download the spotify code for any given track.'''
    # create the code url
    code_url = f'https://scannables.scdn.co/uri/plain/{format}/{background_color_as_hex}/{code_color_as_text}/{size}/{uri}'
    
    return code_url


def create_spotify_code(uri:str, filename:str, code_color_as_text:str = 'black', background_color_as_hex:str = 'FFFFFF', format:str = 'png', size:int = 1024):
    '''Creates a scannable spotify code for any given track given its URI'''
    # the spotify API does not provide codes yet, so we have to build our own code url
    code_url = __create_spotify_code_url(uri=uri, code_color_as_text=code_color_as_text, background_color_as_hex=background_color_as_hex, format=format, size=size)

    # create the code and save it
    urllib.request.urlretrieve(url=code_url, filename=filename)

    return code_url, filename


def find_epoch(year:int) -> str:
    '''Return the epoch for any given year.
    Input:
        - year: integer
    Output:
        - epoch: string
    '''
    epoch = None

    if year > 2019:
        epoch = '2020er'
    elif year > 2009:
        epoch = '2010er'
    elif year > 1999:
        epoch = '2000er'
    elif year > 1989:
        epoch = '90er'
    elif year > 1979:
        epoch = '80er'
    elif year > 1969:
        epoch = '70er'
    elif year > 1959:
        epoch = '60er'
    elif year > 1949:
        epoch = '50er'
    elif year < 1949:
        epoch = 'Oldies'
    
    return epoch


def modify_song_contributor_id(playlist:pd.DataFrame, replace_dict:dict, column:str, modify_column:str) -> pd.DataFrame:
    '''Change the contributor ID for a song in playlist based on a dictionary that maps song title to correct contributor ID.
    Inputs:
        - playlist: pandas.Dataframe. Dataframe received from call to spotify API
        - replace_dict: dictionary. Maps song title to the correct contributor ID (only include songs, whose contributors are to be changed)
        - column: string. Name of the column that contains song titles
        - modify_column: string. Name of the column that is to be modified

    Outputs:
        - playlist_copy: pandas.Dataframe. Copy of playlist dataframe with modified column
    '''
    # create a copy of the dataframe
    playlist_copy = playlist.copy()
    
    # create an empty list to store results
    contributor_ids = []

    # exctract all song titles from the dictionary
    songs = list(replace_dict.keys())

    # find the correct contributor of a song
    for _ , row in playlist.iterrows():
        id = row[modify_column]
        if row[column] in songs:
            id = replace_dict[row[column]]

        contributor_ids.append(id)

    playlist_copy[modify_column] = contributor_ids

    return playlist_copy


def add_contributor_names(playlist:pd.DataFrame, replace_dict:dict, column:str, append_column:str) -> pd.DataFrame:
    '''Add a new column to playlist with the clear name of a contributor.
    Inputs:
        - playlist: pandas.Dataframe. Dataframe received from call to spotify API
        - replace_dict: dictionary. Maps contributor IDs to the clear name of the contributor
        - column: string. Name of the column that contains contributor IDs
        - append_column: string. Name of the column that is to be added to the dataframe

    Outputs:
        - playlist_copy: pandas.Dataframe. Copy of the playlist dataframe with an additional column
    '''
    # create a copy of the dataframe
    playlist_copy = playlist.copy()
    
    # create a list of contributor names
    contributor_names = [replace_dict[row[column]] for _ , row in playlist_copy.iterrows()]

    # add new column to copy of dataframe
    playlist_copy[append_column] = contributor_names

    return playlist_copy


def extract_release_year(playlist:pd.DataFrame, column:str, append_column:str) -> pd.DataFrame:
    '''Add a new column to playlist with the release year of a song
    Inputs:
        - playlist: pandas.Dataframe. Dataframe received from call to spotify API
        - column: string. Name of the column in playlist that contains release dates
        - append_column: string. Name of the column that is to be added to the dataframe

    Outputs:
        - playlist_copy: pandas.Dataframe. Copy of playlist dataframe with an additional column
    '''
    # create a copy of the dataframe
    playlist_copy = playlist.copy()

    # create an empty list to store results
    release_years = []

    # extract release year from release date string
    for release_date in playlist_copy[column]:
        try:
            release_years.append(datetime.strptime(release_date, '%Y-%m-%d').year)
        except ValueError:
            try:
                release_years.append((datetime.strptime(release_date, '%Y-%m')).year)
            except ValueError:
                release_years.append((datetime.strptime(release_date, '%Y')).year)

    # add new column to copy of dataframe
    playlist_copy[append_column] = release_years

    return playlist_copy


def modify_release_year(playlist:pd.DataFrame, replace_dict:dict, release_year_column:str, song_column:str, append_column:str) -> pd.DataFrame:
    '''Change the release year for a song in playlist based on a dictionary that maps song title to correct release year. Useful for remastered versions of songs etc. 
    Inputs:
        - playlist: pandas.Dataframe. Dataframe received from call to spotify API
        - song_to_contributor_id_dict: dictionary. Maps song title to the correct contributor ID (only include songs, whose contributors are to be changed)
        - release_year_column: string. Name of the column that contains release years
        - song_column: string. Name of the column that contains the song titles
        - append_column: string. Name of the column that is to be added to the dataframe

    Outputs:
        - playlist_copy: pandas.Dataframe. Copy of playlist dataframe with an additional column
    '''
    # create a copy of the dataframe
    playlist_copy = playlist.copy()

    # add new column with original release year (spotify has lots of duplicate/remastered songs from diffrent albums)
    original_release_years = []
    songs = list(replace_dict.keys())
    for _ , row in playlist_copy.iterrows():
        year = row[release_year_column]
        if row[song_column].lower() in songs:
            year = replace_dict[row[song_column].lower()]

        original_release_years.append(year)

    playlist_copy[append_column] = original_release_years

    return playlist_copy


def summarize_dataframe(df:pd.DataFrame) -> dict:
    '''Create a comprehensive summary of a pandas Dataframe'''
    keys = df.columns.to_list()

    summary = {key:len(df[key].unique()) for key in keys}

    summary['info'] = f'\n---------------------- SUMMARY ----------------------\nSongs: {summary['song']}\nArtists: {summary['artist']}\nContributors: {summary['contributor_name']} {df['contributor_name'].unique()}\nEpochs: {summary['epoch']} {df['epoch'].unique()}\n-----------------------------------------------------\n'

    n = 0
    n_songs_by_epoch = '\n---------------------- NUMBER OF SONGS BY EPOCH ----------------------'
    for epoch in df['epoch'].unique():
        n_songs = len(df[df['epoch']==epoch])
        n_songs_by_epoch = f'{n_songs_by_epoch}\nSongs from the {epoch}: {n_songs}'

        n += n_songs

    n_songs_by_epoch = f'{n_songs_by_epoch}\nTotal songs: {n}\n'

    summary['number_of_songs_by_epoch'] = n_songs_by_epoch


    songs_by_epoch = f'\n---------------------- SONGS BY EPOCH ----------------------'
    for epoch in df['epoch'].unique():
        songs_by_epoch = f'{songs_by_epoch}\n\n---------------- {epoch} ----------------'
        songs = df['song'][df['epoch']==epoch].to_list()
        for song in songs:
            songs_by_epoch = f'{songs_by_epoch}\n{song}'

    summary['songs_by_epoch'] = songs_by_epoch

    n_songs_by_contributor = '\n---------------------- NUMBER OF SONGS BY CONTRIBUTOR ----------------------'
    for name in df['contributor_name'].unique():
        n_songs = len(df[df['contributor_name']==name])
        n_songs_by_contributor= f'{n_songs_by_contributor}\nSongs added by {name}: {n_songs}'

    n_songs_by_contributor = f'{n_songs_by_contributor}\n'

    summary['number_of_songs_by_contributor'] = n_songs_by_contributor


    return summary


ID_TO_NAME = {'Maria': 'Maria',
              'Max': 'Max',
              'aron.rogmann': 'Aron',
              'hofmann.wiebke': 'Wiebke',
              'nina.brueggmann': 'Nina',
              '9t0xn2xj37wwuk7cwl7sesuxb': 'Nelin',
              's1b2frokt07117g0c53zjn6q5': 'Robert',
              '1133342360': 'Anne',
              'lamoniver': 'Ramona',
              'rexgameboy': 'Finn',
              '31ejeyo5wk7nxsbbmthdldqzaaje': 'Najua',
              'Josi': 'Josi',
              '1159201130': 'Camilla',
              'paula.rulff': 'Hanna',
              'beate.brueggmann': 'Beate'}

SONG_TO_CONTRIBUTOR = {'Norwegian Wood (This Bird Has Flown) - Remastered 2009': 'Maria',
     'Hotel California': 'Maria',
     'I Will Survive': 'Maria',
     'Jump': 'Maria',
     'Forever Young' : 'Maria',
     'Blue (Da Ba Dee) - Gabry Ponte Video Edit': 'Maria',
     'Seven Nation Army': 'Maria',
     'Greek Tragedy': 'Maria',
     'Zacharia': 'Maria',
     'the last great american dynasty': 'Maria',
     'Willst du': 'Max',
     'Save The World': 'Max',
     'Funky Town': 'Max',
     'Pac-Man Fever': 'Max',
     'ocean eyes': 'Max',
     'The Spins': 'Max',
     'Miami': 'Max',
     'Anders': 'Max',
     'Fireflies': 'Max',
     'KIDS': 'Max',
     'Bohemian Rapsody - Remastered 2011': 'hofmann.wiebke',
     'Tiny Dancer': 'nina.brueggmann',
     'Like a Prayer': 'nina.brueggmann',
     'The Logical Song - Remastered 2010': 'nina.brueggmann',
     'Lieben wir': 'Josi',
     'Fame': 'Josi',
     'Call Me Maybe': 'Josi',
     'Can\'t Fight The Moonlight': 'Josi',
     'She\'s Got That Light': 'Josi',
     'As I Lay Me Down': 'Josi',
     'Losing My Religion': 'Josi',
     'Come On Eileen': 'Josi',
     'Living Next Door to Alice': 'Josi',
     'Bad Moon Rising': 'nina.brueggmann'
     }

SONG_TO_YEAR = {'das ist berlin': 1978,
                'heart of gold': 1972,
                'intergalactic': 1998,
                'i\'m every woman': 1978,
                'funky town': 1979,
                'pac-man fever': 1982,
                'lose yourself': 2002,
                'ain\'t no mountain high enough': 1967,
                'i want you back': 1969,
                'billie jean': 1982,
                'don\'t stop believin\'': 1981,
                'smoke on the water': 1971,
                'hypnotize': 1997,
                'enjoy the silence': 1990,
                'it\'s a sin': 1987,
                'stumblin\' in': 1980,
                'geklont': 2001,
                'personal jesus': 1990,
                'house of the rising sun': 1964,
                'jump': 1984,
                'bohemian rhapsody': 1975,
                'das bisschen haushalt... sagt mein mann': 1977
                }


def print_progress_bar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()