# coding: utf-8

import json
import time
from bs4 import BeautifulSoup as bs
import bs4
import os
import pandas as pd
import utilities
import copy
import shutil
import datetime
import requests
import urllib3
import pickle
import calendar
import re


def get_page_comment_data(raw_comments_soup):
    
    comments_html = raw_comments_soup.find_all('li', {'class': 'd-comment'})
    comments_li = []
    for ix, comment_html in enumerate(comments_html):
        d = {}
        d['commenter'] = comment_html.attrs['data-comment-author']
        d['commenter_id'] = comment_html.attrs['data-comment-author-id']
        d['comment_id'] = comment_html.attrs['data-comment-id']
        d['comment'] = ' '.join([x.text for x in comment_html.find_all('p')])
        d['comment_replies'] = comment_html.attrs['data-comment-replies']
        d['comment_timestamp'] = comment_html.attrs['data-comment-timestamp']
        d['comment_highlighted'] = comment_html.attrs['data-comment-highlighted']
        try:
            d['upvotes'] = comment_html.find('div', {'class': 'd-comment__recommend'}).attrs['data-recommend-count']
        except:
            d['upvotes'] = '0'
        comment_reply_to = comment_html.find("a", href=lambda href: href and href.startswith("#comment-"))
        if comment_reply_to is not None:
            d['comment_reply_to_id'] = comment_reply_to.attrs['href'].replace('#comment-', '')
        else:
            d['comment_reply_to_id'] = ''
        comments_li.append(d)
    
    return comments_li

def main():

    site = 'guardian'

    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Load and concatenate files')

    dict_srcs = [x for x in utilities.get_files(utilities.blm_html_1pass_dir) if 'guardian' in x]
    dates_articles_ = utilities.combine_dicts(dict_srcs)
    utilities.count_articles(dates_articles_)


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Parse comments')

    dates_articles = copy.deepcopy(dates_articles_)
    for date, days_articles in dates_articles_.items():
        for ix, article in enumerate(days_articles):
            raw_comments_pages = article['raw_comments']
            parsed_comments_li = []
            for raw_comments_page in raw_comments_pages:
                raw_comments_soup = bs(raw_comments_page)
                parsed_comments = get_page_comment_data(raw_comments_soup)
                parsed_comments_li += parsed_comments
            dates_articles[date][ix]['parsed_comments'] = parsed_comments_li


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Save outputs, one json per year')

    years = sorted(list(set([x.split('-')[0] for x in dates_articles.keys()])))
    dst_dir = os.path.join(utilities.blm_processed_parsed_dir, '2nd_iteration')
    for year in years:
        dates_articles2 = {}
        dst = os.path.join(dst_dir, site + '_' + year + '.json')
        for date, days_articles in dates_articles.items():
            if year in date:
                date2 = copy.deepcopy(date)
                dates_articles2[date2] = copy.deepcopy(days_articles)
        with open(dst, 'w') as f:
            json.dump(dates_articles2, f)


if __name__ == '__main__':
    main()
