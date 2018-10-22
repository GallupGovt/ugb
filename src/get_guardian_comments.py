# coding: utf-8

import utilities
from utilities import preview
from bs4 import BeautifulSoup as bs
import bs4
import os
import copy
import datetime
import requests
import pickle


def get_page_comments(comments_url):
    r = requests.get(comments_url)
    comments_soup = bs(r.text)
    comments = str(comments_soup.find('div', {'class': 'd-discussion'}))
    return comments_soup, comments


def get_next_page_url(comments_soup):
    pagination_list = comments_soup.find('div', {'class': 'pagination__list'})
    if pagination_list is not None:
        next_page = pagination_list.find('a', {'aria-label': 'Comments next page'})
        if next_page is not None:
            return next_page['href']
    return None

def main():

    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    # DEFINE INPUTS AND LOAD DATA

    today_dt = datetime.date.today()
    yesterday_dt = today_dt - datetime.timedelta(days=1)
    dates_ds = pd.date_range('2013-07-01', yesterday_dt)
    dates = [str(x.date()).replace('-', '/') for x in list(dates_ds)]
    overwrite = inputs.overwrite
    site = 'guardian'

    src = os.path.join(utilities.blm_dir, 'Google_CSE_Results', site + '_articles.pkl')
    with open(src, 'rb') as f:
        dates_articles_ = pickle.load(f)
    interim_dir = os.path.join(utilities.blm_dir, 'z_Interim')
    utilities.mkdir(interim_dir)


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Pull comment URLs')

    if overwrite:
        base_url = 'https://www.theguardian.com/discussion'
        dates_articles = copy.deepcopy(dates_articles_)
        counter = 0
        for date, days_articles in dates_articles.items():
            for ix, article in enumerate(days_articles):
                try:
                    article_url = article['url'].strip().lower()
                    r = requests.get(article_url)
                    article_soup = bs(r.text)
                    comments_div = article_soup.find('div', {'id': 'comments'})
                    soup_id = comments_div.attrs['data-discussion-key']

                    comments_url = base_url + soup_id
                    dates_articles[date][ix]['comments_url'] = comments_url
                except:
                    dates_articles[date][ix]['comments_url'] = 'no comments'

        dates_articles_dst = os.path.join(interim_dir, 'articles_w_comments_urls.pkl')
        with open(dates_articles_dst, 'wb') as f:
            pickle.dump(dates_articles, f)
    else:
        with open(dates_articles_dst, 'rb') as f:
            dates_articles = pickle.load(f)


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Remove articles with no comments')

    dates_articles2 = {}
    for date, days_articles in dates_articles.items():
        articles = []
        for article in days_articles:
            if article['comments_url'] != 'no comments':
                article_copy = copy.deepcopy(article)
                articles.append(article_copy)
        if len(articles) > 0:
            dates_articles2[date] = articles


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Scrape comments pages')

    if overwrite:
        dates_articles3 = {}
        counter = 0
        file_counter = 0
        for date, days_articles in dates_articles2.items():
            articles3 = []
            for article in days_articles:
                comments_url = article['comments_url']
                comments_li = []

                try:
                    comments_soup, comments = get_page_comments(comments_url)
                    comments_li.append(comments)
                    next_page_comments_url = get_next_page_url(comments_soup)

                    while next_page_comments_url is not None:
                        try:
                            next_page_comments_soup, next_page_comments = get_page_comments(next_page_comments_url)
                            comments_li.append(next_page_comments)
                            next_page_comments_url = get_next_page_url(next_page_comments_soup)
                        except:
                            next_page_comments_url = None
                except:
                    pass
                article3 = copy.deepcopy(article)
                article3['raw_comments'] = comments_li
                articles3.append(article3)
            if len(articles3) > 0:
                dates_articles3[date] = articles3

            counter +=1
            if counter >= 10:
                dst = os.path.join(utilities.blm_html_1pass_dir, site + str(file_counter) + '.pkl')
                with open(dst, 'wb') as f:
                    pickle.dump(dates_articles3, f)
                dates_articles3 = {}
                counter = 0
                file_counter +=1

        if counter > 0:
            dst = os.path.join(utilities.blm_html_1pass_dir, site + str(file_counter+1) + '.pkl')
            with open(dst, 'wb') as f:
                pickle.dump(dates_articles3, f)


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Print outputs')

    recovered_articles_srcs = [x for x in utilities.get_files(utilities.blm_html_1pass_dir) if site in x]
    recovered_articles = utilities.combine_dicts(recovered_articles_srcs)
    n_articles = utilities.count_articles(recovered_articles)
    print('Recovered %s on-topic articles with comments' % n_articles)


if __name__ == '__main__':
    main()
