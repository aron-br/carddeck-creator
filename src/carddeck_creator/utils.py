#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__      = "Aron Brüggmann"
__copyright__   = "Copyright 2023"

"""
utils.py: Some utility functions used in this project
"""

import os
import pandas as pd
import urllib.request
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import musicbrainzngs
from functools import lru_cache
import re

musicbrainzngs.set_useragent(
    "carddeck-creator",
    "1.0",
    "your-email@example.com"
)

def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text.lower()).replace("&", "and").strip()

def extract_spotify_year(track_meta: dict):
    if not track_meta:
        return None

    date = track_meta.get("album", {}).get("release_date")

    if not date:
        return None

    try:
        year = int(date[:4])
    except:
        return None

    # Spotify often returns remaster years → filter heuristic
    album_name = track_meta.get("album", {}).get("name", "").lower()

    if any(x in album_name for x in [
        "remaster", "deluxe", "anniversary", "edition"
    ]):
        return None  # ignore unreliable Spotify year

    return year


@lru_cache(maxsize=1000)
def get_musicbrainz_year(song: str, artist: str):
    try:
        result = musicbrainzngs.search_recordings(
            recording=song,
            artist=artist,
            limit=3
        )

        recordings = result.get("recording-list", [])

        candidates = []

        for r in recordings:
            releases = r.get("release-list", [])

            for rel in releases:
                title = rel.get("title", "").lower()
                date = rel.get("date")

                if not date:
                    continue

                year = int(date[:4])

                # strongly penalize reissues
                penalty = 0

                if any(x in title for x in [
                    "remaster", "remastered", "reissue", "deluxe", "anniversary", "edition"
                ]):
                    penalty = 1000  # push these far down

                candidates.append((year + penalty, year))

        if not candidates:
            return None

        # choose smallest adjusted score, return real year
        best = min(candidates, key=lambda x: x[0])[1]

        return best

    except Exception:
        return None
    

def choose_best_year(spotify_year, mb_year, old_year):
    """
    Strong bias toward earliest plausible year.
    """

    candidates = [y for y in [spotify_year, mb_year, old_year] if y is not None]

    if not candidates:
        return None

    return min(candidates)


def get_correct_release_year(song, artist, spotify_meta, old_year):
    spotify_year = extract_spotify_year(spotify_meta)

    mb_year = get_musicbrainz_year(song, artist)

    return choose_best_year(spotify_year, mb_year, old_year)


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
    elif year <= 1949:
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


def validate_and_fix_release_years(
        playlist: pd.DataFrame,
        spotify_gateway,
        song_column: str = "song",
        artist_column: str = "artist",
        overwrite: bool = True
) -> pd.DataFrame:

    playlist_copy = playlist.copy()

    corrected_years = []
    change_log = []

    total = len(playlist_copy)

    for i, (_, row) in enumerate(playlist_copy.iterrows(), start=1):

        song = row[song_column]
        artist = row[artist_column]
        old_year = row.get("release_year_raw")

        meta = spotify_gateway.get_track_metadata(song, artist)

        new_year = get_correct_release_year(song, artist, meta, old_year)

        # log any changes
        if old_year != new_year:
            change_log.append({
                "song": song,
                "artist": artist,
                "old_year": old_year,
                "new_year": new_year
            })

        corrected_years.append(new_year)

        print_progress_bar(
            iteration=i,
            total=total,
            prefix="Validating years",
            suffix=f"{i}/{total}",
            length=40
        )

    print()

    # FINAL COLUMN ONLY
    playlist_copy["release_year"] = corrected_years
    

    return playlist_copy, change_log


def summarize_dataframe(
        df: pd.DataFrame,
        export_pdf: bool = True,
        pdf_filename: str = "dataframe_summary.pdf"
):
    """
    Create a comprehensive dataframe summary
    and export a visually enhanced PDF report.
    """

    # -------------------------------------------------
    # CLEAN DATA
    # -------------------------------------------------

    if 'release_year' in df.columns:
        df['release_year'] = pd.to_numeric(
            df['release_year'],
            errors='coerce'
        )

    # -------------------------------------------------
    # BASIC METRICS
    # -------------------------------------------------

    n_songs = len(df)

    n_artists = df['artist'].nunique()

    n_contributors = df['contributor_name'].nunique()

    oldest_year = int(df['release_year'].min())

    latest_year = int(df['release_year'].max())

    # -------------------------------------------------
    # CHART DATA
    # -------------------------------------------------

    # define chronological epoch order
    epoch_order = [
        'Oldies',
        '50er',
        '60er',
        '70er',
        '80er',
        '90er',
        '2000er',
        '2010er',
        '2020er'
    ]

    # group songs by epoch
    songs_per_epoch = (
        df.groupby('epoch')
        .size()
    )

    # reorder epochs chronologically
    songs_per_epoch = songs_per_epoch.reindex(epoch_order).dropna()

    songs_per_contributor = (
        df.groupby('contributor_name')
        .size()
        .sort_values(ascending=False)
    )

    # -------------------------------------------------
    # CREATE CHARTS
    # -------------------------------------------------

    epoch_chart = "songs_by_epoch.png"

    plt.figure(figsize=(8, 5))

    songs_per_epoch.plot(
        kind='bar',
        color='skyblue'
    )

    plt.title("Songs by Epoch")

    plt.xlabel("Epoch")

    plt.ylabel("Number of Songs")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(epoch_chart)

    plt.close()

    contributor_chart = "songs_by_contributor.png"

    plt.figure(figsize=(7, 7))

    songs_per_contributor.plot(
        kind='pie',
        autopct='%1.1f%%'
    )

    plt.ylabel("")

    plt.title("Songs by Contributor")

    plt.tight_layout()

    plt.savefig(contributor_chart)

    plt.close()

    # -------------------------------------------------
    # CREATE PDF
    # -------------------------------------------------

    if export_pdf:

        pdf = FPDF()

        pdf.set_auto_page_break(
            auto=True,
            margin=15
        )

        # -------------------------------------------------
        # TITLE PAGE
        # -------------------------------------------------

        pdf.add_page()

        pdf.set_font("Arial", "B", 22)

        pdf.cell(
            0,
            20,
            "Music Dataset Summary Report",
            ln=True,
            align='C'
        )

        pdf.ln(10)

        # -------------------------------------------------
        # OVERVIEW TABLE
        # -------------------------------------------------

        pdf.set_font("Arial", "B", 14)

        pdf.cell(
            0,
            10,
            "Dataset Overview",
            ln=True
        )

        pdf.set_font("Arial", "", 12)

        overview_rows = [
            ("Songs", n_songs),
            ("Artists", n_artists),
            ("Contributors", n_contributors),
            ("Oldest Release Year", oldest_year),
            ("Latest Release Year", latest_year)
        ]

        for label, value in overview_rows:

            pdf.set_font("Arial", "B", 11)

            pdf.cell(70, 8, str(label), border=1)

            pdf.set_font("Arial", "", 11)

            pdf.cell(50, 8, str(value), border=1, ln=True)

        pdf.ln(10)

        # -------------------------------------------------
        # EPOCH TABLE
        # -------------------------------------------------

        pdf.set_font("Arial", "B", 14)

        pdf.cell(
            0,
            10,
            "Songs by Epoch",
            ln=True
        )

        pdf.set_font("Arial", "B", 11)

        pdf.cell(80, 8, "Epoch", border=1)

        pdf.cell(40, 8, "Songs", border=1, ln=True)

        pdf.set_font("Arial", "", 11)

        for epoch, count in songs_per_epoch.items():

            pdf.cell(80, 8, str(epoch), border=1)

            pdf.cell(40, 8, str(count), border=1, ln=True)

        pdf.ln(10)

        # -------------------------------------------------
        # ADD BAR CHART
        # -------------------------------------------------

        pdf.set_font("Arial", "B", 14)

        pdf.cell(
            0,
            10,
            "Songs by Epoch Chart",
            ln=True
        )

        pdf.image(
            epoch_chart,
            w=170
        )

        pdf.ln(10)

        # -------------------------------------------------
        # ADD PIE CHART
        # -------------------------------------------------

        pdf.set_font("Arial", "B", 14)

        pdf.cell(
            0,
            10,
            "Contributor Distribution",
            ln=True
        )

        pdf.image(
            contributor_chart,
            w=140
        )

        pdf.ln(10)

        # -------------------------------------------------
        # SONG LISTS
        # -------------------------------------------------

        pdf.add_page()

        pdf.set_font("Arial", "B", 16)

        pdf.cell(
            0,
            10,
            "Songs by Epoch",
            ln=True
        )

        for epoch in epoch_order:
    
            # skip empty epochs
            if epoch not in df['epoch'].values:
                continue

            pdf.ln(5)

            pdf.set_font("Arial", "B", 13)

            pdf.cell(
                0,
                8,
                str(epoch),
                ln=True
            )

            pdf.set_font("Arial", "", 11)

            songs = df[df['epoch'] == epoch]['song']

            for song in songs:

                clean_song = str(song).encode(
                    "latin-1",
                    "replace"
                ).decode("latin-1")

                pdf.multi_cell(
                    0,
                    6,
                    f"- {clean_song}"
                )

        # -------------------------------------------------
        # EXPORT
        # -------------------------------------------------

        pdf.output(pdf_filename)

        print(
            f"\nEnhanced PDF report exported: {pdf_filename}"
        )

    # -------------------------------------------------
    # CLEAN TEMP FILES
    # -------------------------------------------------

    if os.path.exists(epoch_chart):
        os.remove(epoch_chart)

    if os.path.exists(contributor_chart):
        os.remove(contributor_chart)

    # -------------------------------------------------
    # RETURN SUMMARY DICT
    # -------------------------------------------------

    return {
        "songs": n_songs,
        "artists": n_artists,
        "contributors": n_contributors,
        "oldest_release_year": oldest_year,
        "latest_release_year": latest_year
    }


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

SONG_TO_CONTRIBUTOR = {
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