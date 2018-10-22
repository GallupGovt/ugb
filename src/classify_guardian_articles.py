# coding: utf-8

import config
import inputs
import utilities
from utilities import preview
import os
import pandas as pd
import copy
import pickle
import keyring
import getpass
from googleapiclient.discovery import build


dates_ds = pd.date_range(inputs.start_date, inputs.end_date)
dates = [str(x.date()).replace('-', '/') for x in list(dates_ds)]
overwrite = inputs.overwrite
site = 'guardian'
dst_dir = os.path.join(utilities.blm_dir, 'Google_CSE_Results')
utilities.mkdir(dst_dir)
res_dst = os.path.join(dst_dir, site + '_res_li.pkl')


def main():
    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Use google custom search api to retrieve on-topic articles for selected site')
    # indicate the site on the google custom search api control panel

    # enter credentials from config.py file
    # if this file doesn't exist, create one and define google_custom_search_cx and developerKey variables
    cx = config.google_custom_search_cx
    developerKey = config.google_custom_search_developer_key
    service = build("customsearch", "v1", developerKey=developerKey)

    # make date ranges
    begin_mo, end_mo = [list([str(x.date()).replace('-', '') for x in pd.date_range('2013-07-01', '2018-08-31', freq=x)]) for x in ['MS', 'M']]
    dates = [':'.join(['date', 'r', x[0], x[1]]) for x in list(zip(begin_mo, end_mo))]

    # define topics
    topics = ['black lives matter', 'police brutality']

    # iterate over each topic, srp, and dates
    starts = np.arange(1, 100, 10)
    res_li = []
    for topic in topics:
        for start in starts:
            for date in dates:
                if start == 91:
                    num = 9
                else:
                    num = 10
                res = service.cse().siterestrict().list(
                     q=topic
                    ,cx=cx
                    ,hl='lang_en'
                    ,lr='lang_en'
                    ,num=num
                    ,start=start
                    ,sort=date
                    ).execute()
                res_li.append(res)
    if overwrite:
        with open(res_dst, 'wb') as f:
            pickle.dump(res_li, f)


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Build final dataframe and save to disk')
    df_res = []
    for srp in res_li:
        try:
            articles = srp['items']
            for article in articles:
                df_res.append([article['title'], article['link']])
        except:
            pass

    df_res = pd.DataFrame(df_res, columns=['title', 'link']).drop_duplicates().set_index('title')
    if overwrite:
        df_res.to_pickle(os.path.join(dst_dir, site + '_blm_links.pkl'))

    preview(df_res)


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Filter out off-topic articles and save that to disk')

    # combine dictionaries
    articles_dir = utilities.data_2018_dir
    article_srcs = [x for x in utilities.get_files(utilities.data_2018_dir, extensions=['json']) if site in x]
    dates_articles_ = utilities.combine_dicts(article_srcs)

    links = [x.lower().split('https://www.')[-1] for x in df_res.link.unique().tolist()]
    dates_articles = {}
    for date, days_articles in dates_articles_.items():
        articles = []
        for article in days_articles:
            article2 = copy.deepcopy(article)
            try:
                link = article2['url'].lower().strip().split('http://www.')[-1]
            except:
                link = ''
            if link in links:
                articles.append(article2)
        if len(articles) > 0:
            dates_articles[date] = articles

    articles_dst = os.path.join(dst_dir, site + '_articles.pkl')
    with open(articles_dst, 'wb') as f:
        pickle.dump(dates_articles, f)


if __name__ == '__main__':
    main()
