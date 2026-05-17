#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__      = 'Aron Brüggmann'
__copyright__   = 'Copyright 2023, Aron Brüggmann'

'''
carddeck.py: Implements a custom class that uses the spotify api to query songs and song metadata from a public spotify playlist.

It builds on top of the spotipy library and requires a custom spotify application (check out https://developer.spotify.com/documentation/web-api/concepts/apps
if you don't have an app already) with a client ID and client secret as well as the ID of the public spotify playlist you want to download.
'''

import os
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader

class CardDeck():

    def __init__(self, data:pd.DataFrame, content_columns:list, card_template:str, template_fields:list, batch_size:int):
        self.data = data
        self.content_columns = content_columns
        self.card_template = card_template
        self.template_fields = template_fields
        self.batch_size = batch_size
        self.n_batches = int(np.ceil(len(data)/self.batch_size))

        if not len(content_columns) == len(template_fields):
            raise ValueError(f'Error: Arguments content_columns and template_fields must have the same length. Got len(content_columns)={len(self.content_columns)}, len(template_fields)={len(template_fields)}')

        self.__batch_data()
        
        return

    def __batch_data(self):
        '''Split dataframe in batches of size self.batch_size'''
        # split DataFrame into chunks
        batched_data = [self.data[i:i+self.batch_size] for i in range(0, len(self.data), self.batch_size)]
        
        # create an empty list to store data
        batches = []

        # fill batches dict
        for batch in batched_data:
            card_batch = []
            for _, row in batch.iterrows():
                card_content = {}

                for i, field in enumerate(self.template_fields):
                    card_content[field] = row[self.content_columns[i]]

                card_batch.append(card_content)

            batches.append(card_batch)
        
        if len(batches[-1]) < self.batch_size:
            empty_card_content = {}
            for i, field in enumerate(self.template_fields):
                empty_card_content[field] = ''

            for _ in range(self.batch_size-len(batches[-1])):
                batches[-1].append(empty_card_content)

        self.batches = batches

        return
    
    def create_cards(self, filename:str):
        '''Create a printable deck of cards in the style of card_template'''
        # check file extension
        _, file_extension = os.path.splitext(filename)
        if not filename.lower().endswith(('.html')):
            raise ValueError(f'Error. Invalid file extension. Expected: \'.html\'; Got: \'{file_extension}\'')
        
        # load templates folder to environment (security measure)
        env = Environment(loader=FileSystemLoader(os.path.dirname(self.card_template)))

        # load the `index.jinja` template
        index_template = env.get_template(os.path.basename(self.card_template))
        output_from_parsed_template = index_template.render(batches=self.batches)

        # write the parsed template
        with open(filename, "w") as page:
            page.write(output_from_parsed_template)

        return
    

if __name__ == '__main__':
    data = pd.read_csv('/Users/aronrogmann/PythonProjects/carddeck-creator/results/datasets/playlist_processed.csv')
    card_template = os.path.join(os.getcwd(), 'src/carddeck_creator/static/templates/card_template_A4_v2.jinja')

    card_deck = CardDeck(data=data,
                         content_columns=['song', 'original_release_year', 'artist', 'contributor_name', 'number', 'code_file'],
                         card_template=card_template,
                         batch_size=9,
                         template_fields=['text1', 'text2', 'text3', 'smallText', 'number', 'backImage'])
    
    card_deck.create_cards(filename='./cards_v2.html')

    print('Done')