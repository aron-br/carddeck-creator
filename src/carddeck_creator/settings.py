#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__      = 'Aron Brüggmann'
__copyright__   = 'Copyright 2023, Aron Brüggmann'

'''
settings.py: Centralized configuration for the carddeck-creator.

This file provides a collection of constants used throughout this project, ensuring a unified and easily modifiable configuration.
By centralizing these values, the main class code remains clean and changes in configuration can be made in this dedicated location.
Project specific settings can to be adapted for your project. The fixed settings should never be modified.
'''
# ------------------------- PROJECT SPECIFIC SETTINGS !CAN BE MODIFIED! -------------------------
# Define spotify playlist ID (replace by your PLAYLIST-ID)
PLAYLIST_ID = '0QoUa07l09WLh0ZTxBvgX4'

# Define a directory, where all results are saved to (DEFAULT: './results/')
RESULT_FOLDER = './results/'

# ------------------------- FIXED SETTINGS !DO NOT CHANGE! -------------------------
# define the subdirectories
IMAGE_FOLDER = f'{RESULT_FOLDER}images/'
DATA_FOLDER = f'{RESULT_FOLDER}datasets/'
HTML_FOLDER = f'{RESULT_FOLDER}htmls/'
PDF_FOLDER = f'{RESULT_FOLDER}pdfs/'

# create a list of all directories and subdirectories
FOLDERS = [RESULT_FOLDER, IMAGE_FOLDER, DATA_FOLDER, HTML_FOLDER, PDF_FOLDER]