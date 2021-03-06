import numpy as np
import pandas as pd
from PIL import Image
from io import BytesIO
import requests
import re
import warnings
from classes.base import Data_Scraping
warnings.filterwarnings("ignore")

"""
Some Key notes:
    
uri points you to the individual json object where you can locate all info on the data
download_uri points you to the actual json data for the cards.
    
Included Functions:

cleaning_scryfall_data: Reads in dataframe from base.py and cleans it. Focuses on if statements, to allow flexibility in use.
Input on this is fixed, but allows users to change the direction of the call so it can call to other sites as well as other frames provided by scryfall.

modeling_prep_mtg_oracle: Performs basic modeling preparation for the scryfall dataset. Goal is to create a recommendation model for users to build decks.

img_get: retrieves images from their uri's and posts them for user to view
"""
    
class Data_Handling(Data_Scraping):
    def __init__(self):
        super().__init__()
    
    def cleaning_scryfall_data(self, n = 'oracle_cards'):
        self.df = super().get_data_with(n = n)
            
        if 'edhrec_rank' in self.df.columns:
            edh_fix = self.df[self.df['edhrec_rank'].isna() == True]
            counter = 22665 # Max rank + 1
    
            edh_fix.edhrec_rank = range(counter, (counter + len(edh_fix)))
            self.df.loc[edh_fix.index, :] = edh_fix[:]
            self.df['edhrec_rank'] = self.df['edhrec_rank'].astype('int64')
    
        # Fix power column
        if 'power' in self.df.columns:
            self.df['power'].loc[self.df['power'].isna() == True] = 0
        
        # Fix Toughness Columns
        if 'toughness' in self.df.columns:
            self.df['toughness'].loc[self.df['toughness'].isna() == True] = 0
            
        # Fix CMC Column
        if 'cmc' in self.df.columns:
            self.df['cmc'].loc[17411] = 1
            self.df['cmc'] = self.df['cmc'].astype('int64')
        
        if 'oracle_id' in self.df.columns:
            self.df.set_index('oracle_id', inplace=True)
        
        if 'colors' in self.df.columns:
            self.df['colors'] = self.df['colors'].str[0]
            self.df['colors'].fillna('C', inplace=True)

        if 'color_identity' in self.df.columns:
            self.df['color_identity'] = self.df['color_identity'].str[0]
            self.df['color_identity'].fillna('C', inplace=True)
            
        if 'keywords' in self.df.columns:
            self.df['keywords'] = self.df['keywords'].str[0]
            self.df['keywords'].fillna('None', inplace =True)
        
        if 'mana_cost' in self.df.columns:
            self.df['mana_cost'].fillna(self.df['cmc'].astype(str), inplace=True)
           
            l = []
            for val in self.df.mana_cost:
                val = re.sub(r'[{]', '', str(val))
                val = re.sub(r'[}]', '/', val)
                val = val.strip('/')
                l.append(val)
            self.df['mana_cost'] = l
            self.df['mana_cost'] = np.where(self.df['mana_cost'] == '', self.df['cmc'], self.df['mana_cost'])
        

            
        return self.df
    
    def modeling_prep_mtg_oracle(self, df):
        # Drop columns for modeling purposes
        drop_cols = ['id', 'multiverse_ids', 'tcgplayer_id', 'cardmarket_id', 'lang', 'object', 
                     'released_at', 'uri', 'scryfall_uri', 'layout', 'highres_image', 'image_status', 
                     'image_uris', 'games', 'frame', 'full_art', 'textless', 'booster', 'story_spotlight', 'prices',
                     'legalities', 'reserved', 'foil', 'nonfoil', 'card_back_id', 'artist', 'artist_ids', 'illustration_id', 
                     'border_color', 'oversized', 'finishes', 'scryfall_set_uri', 'rulings_uri', 'promo', 'set', 'set_uri', 'set_search_uri', 
                     'reprint', 'variation', 'set_id', 'prints_search_uri', 'collector_number', 'digital', 'mtgo_id']
        
        if 'oracle_text' in self.df.columns:
            self.df['oracle_text'].dropna(inplace=True)
            
        if 'related_uris' in self.df.columns:
            target_cards = self.df['related_uris']
            drop_cols.append('related_uris')
        
        if 'type_line' in df.columns:
            a = self.df[self.df['type_line'].str.contains('Token Creature')]
            self.df.drop(labels=a.index, inplace=True)
                
        if 'set_name' in df.columns:
            c = self.df[self.df['set_name'].str.contains('Art Series')]
            self.df.drop(labels = c.index, inplace=True)
        
        # Drop a million mana_cost card from UnHinged(joke set)
        self.df.drop(index = df[df['name'] == 'Gleemax'].index,inplace=True)
            
        drop_cols_high_nan = [col for col in self.df.columns if (self.df[col].isna().sum() / len(self.df) *100) > 35]
        self.df.drop(columns = drop_cols_high_nan, inplace = True)
        self.df.drop(columns = drop_cols, inplace = True)

        return self.df, target_cards
    
    def img_return(self,card_name : str):
        img_str = self.df[self.df['name'] == card_name]['image_uris'][0]['normal']
        response = requests.get(img_str)
        img = Image.open(BytesIO(response.content))
        return img

if __name__ == '__main__':
    dh = Data_Handling()
    print("Data Handling has been instantiated")
    df = dh.cleaning_scryfall_data()
    print("Successfully created DataFrame Object")
    df = dh.modeling_prep_mtg_oracle(df)
    print("Finished with Model Prep for Data")
