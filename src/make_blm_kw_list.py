# coding: utf-8

import inputs
import utilities
from utilities import preview
import datamaps
import pandas as pd
import os



wp_shootings_db_path = os.path.join(utilities.blm_external_dir, 'wp_shootings_db.csv')
overwrite = inputs.overwrite

def main(overwrite=overwrite, wp_shootings_db_path=wp_shootings_db_path):
    """Download Washington Post police shootings dataset and append to custom list of BLM / Police Brutality kws.
    Function returns 1) blm_kws and 2) exclude_kws"""
    
    
    # get washington post data
    if (not os.path.isfile(wp_shootings_db_path)) or (overwrite==True): 
        url = 'https://raw.githubusercontent.com/washingtonpost/data-police-shootings/master/fatal-police-shootings-data.csv'
        wp_shootings_db_ = pd.read_csv(url)
        wp_shootings_db_.to_csv(wp_shootings_db_path)
    else:
        wp_shootings_db_ = pd.read_csv(wp_shootings_db_path)

    m = wp_shootings_db_.race=='B'
    wp_shootings_db = wp_shootings_db_.copy()[m]
    wp_shootings_db_kws = wp_shootings_db.name.str.lower().str.strip().unique().tolist()

    # combine lists
    blm_kws = datamaps.blm_kws + wp_shootings_db_kws
    blm_kws = sorted(list(set([x.lower() for x in blm_kws])))

    # # define exclude kws
    exclude_kws = ['affirmative action', 'obamacare', 'climate change', 'david hogg', 'arab spring']
    
    return blm_kws, exclude_kws

if __name__ == '__main__':
    main(overwrite=overwrite, wp_shootings_db_path=wp_shootings_db_path)
