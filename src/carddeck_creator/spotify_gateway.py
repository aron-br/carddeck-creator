#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__      = 'Aron Brüggmann'
__copyright__   = 'Copyright 2023, Aron Brüggmann'

'''
spotify_connector.py: Implements a custom class that uses the spotify api to query songs and song metadata from a public spotify playlist.

It builds on top of the spotipy library and requires a custom spotify application (check out https://developer.spotify.com/documentation/web-api/concepts/apps
if you don't have an app already) with a client ID and client secret as well as the ID of the public spotify playlist you want to download.
'''

import os
import time
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from utils import print_progress_bar, create_spotify_code
from settings import IMAGE_FOLDER


class SpotifyGateway():

    def __init__(self, playlist_id:str):
        self.playlist_id = playlist_id
        self.__authenticate()


    def __authenticate(self):
        '''Authenticate to spotify via the client ID and secret stored as environmental variables.'''
        # authenticate to spotify
        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

        self.spotify = spotify

        return


    def __query_playlist(self):
        '''Query metadata of playlist and save it as a dataframe'''
        # send api call and save response
        self.api_response = self.spotify.playlist_tracks(playlist_id=self.playlist_id)

        return


    def __extract_metadata_from_response(self, max_iterations:int = 5):
        ''' Creates a dataframe by iterating through all the items in the response object that was obtained from a call to the spotify API.'''
        response = self.api_response
        items = response['items']

        # iterate over all items in response (there should be one item for each track in the playlist)
        while response['next']:
            response = self.spotify.next(response)
            items.extend(response['items'])

        # get number of tracks in playlist
        n_tracks = len(items)

        # instantiate an empty dict to store metadata
        keys = ['number', 'song', 'artist', 'release_date', 'contributor_id', 'track_uri']
        data = {key: [] for key in keys}

        # start extracting the results
        counter = 0
        while counter < max_iterations:
            # we have not encountered an error at the start of the loop
            error = None

            # print progess bar to terminal
            print_progress_bar(0, n_tracks, prefix = 'Processing tracks. Progress:', suffix = 'Complete', length = 50)
            
            for i, item in enumerate(items, 1):    
                try:
                    data['number'].append(i)
                    data['song'].append(item['track']['name'])
                    data['artist'].append(item['track']['artists'][0]['name'])
                    data['release_date'].append(item['track']['album']['release_date'])
                    data['contributor_id'].append(item['added_by']['id'])
                    data['track_uri'].append(item['track']['uri'])
                except TypeError as e:
                    # record the error and exit the for loop
                    error = e
                    break
                    
                # update progress bar in each iteration
                print_progress_bar(i, n_tracks, prefix = 'Processing tracks. Progress:', suffix = 'Complete', length = 50)
                
                # not necassary but looks nicer with a small delay
                time.sleep(0.01)
            
            if error is None:
                break

            else:
                print(f'Encountered error when unpacking response: {error}. Retrying in 5 seconds.')
                time.sleep(5)
            
            counter += 1

        # create a dataframe and save it as an instance attribute
        self.playlist = pd.DataFrame(data=data)

        return
    

    def __create_spotify_codes(self):
        '''Add a new column with the url to the spotify code of the corersponding track to an instances playlist attribute.'''
        code_urls = []
        code_files = []

        # get length of playlist
        n_tracks = len(self.playlist)

        # print progess bar to terminal
        print_progress_bar(0, n_tracks, prefix = 'Processing codes. Progress:', suffix = 'Complete', length = 50)

        for i, uri in enumerate(self.playlist['track_uri'], 1):
            filename = os.path.join(IMAGE_FOLDER, f'{i}.png')
            code_url, code_file = create_spotify_code(uri=uri, filename=filename)

            code_urls.append(code_url)
            code_files.append(code_file)

            # update progress bar in each iteration
            print_progress_bar(i, n_tracks, prefix = 'Processing codes. Progress:', suffix = 'Complete', length = 50)

        self.playlist['code_url'] = code_urls
        self.playlist['code_file'] = code_files

        return


    def get_playlist_metadata(self):
        ''' Use the spotify API to query playlist metadata, format the metadata as a dataframe.'''
        # query metadata using the spotify API
        self.__query_playlist()

        # extract metadata from response
        self.__extract_metadata_from_response()

        # add spotify code URLs to the dataframe
        self.__create_spotify_codes()

        return



if __name__ == '__main__':
    from settings import PLAYLIST_ID

    # create an instace of spotify gateway
    sc = SpotifyGateway(playlist_id=PLAYLIST_ID)
    
    # call API to download metadata
    sc.get_playlist_metadata()

    # print playlist dataset to console
    print(sc.playlist)