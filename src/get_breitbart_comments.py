# coding: utf-8

import utilities
from utilities import preview
import make_blm_kw_list
import json
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
import bs4
import os
import pandas as pd
import copy
import shutil
import datetime
import requests
import urllib3
import pickle
import calendar
from collections import defaultdict
import numpy as np


today_dt = datetime.date.today()
yesterday_dt = today_dt - datetime.timedelta(days=1)
dates_ds = pd.date_range('2013-07-01', yesterday_dt)
dates = [str(x.date()).replace('-', '/') for x in list(dates_ds)]
site = 'breitbart'
articles_dir = utilities.data_2018_dir
article_srcs = [x for x in utilities.get_files(articles_dir, extensions=['json']) if site in x]
blm_dir = utilities.blm_dir
blm_html_1pass_dir = utilities.blm_html_1pass_dir



# instantiate driver
def instantiate_driver(wait=10, url='https://google.com', headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    driver_path = os.path.join(r'G:\Strengths_Reporting\code\src\tools', 'chromedriver.exe')
    driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
    driver.get(url)
    driver.maximize_window()
    driver.implicitly_wait(wait)
    return driver


def get_iframe_text(url, sleep=0.5, wait=2):
    
    def get_n_comments(soup):
        try:
            return int(soup.find('a', {'class': 'byC'}).contents[0].replace(',', ''))
        except:
            return 0
    
    # instantiate driver and navigate to url
    try:
        driver = instantiate_driver(url=url)
    # deal with bad urls
    except:
        driver.quit()
        return 'Error with comments URL'
    
    # only get comments for articles that have at least one comment
    soup = bs(driver.page_source)
    n_comments = get_n_comments(soup)
    if n_comments > 0:
        # find comments iframe
        xpath = "//iframe[starts-with(@id, 'dsq-app')]"
        iframe = WebDriverWait(driver, wait).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, xpath)))
        # load all the comments
        while True:
            try:
                driver.switch_to_default_content()
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") 
                xpath = "//iframe[starts-with(@id, 'dsq-app')]"
                iframe = WebDriverWait(driver, wait).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, xpath)))
                css_selector = '[data-action="more-posts"]' 
                WebDriverWait(driver, wait).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))).click()
            finally:  # if there are no more comments to click, break out of while loop
                break

        # we exit the while loop with the driver switched to the comments iframe, which is what we want
        iframe_soup = bs(driver.page_source)
        driver.quit()
        return iframe_soup.get_text()
    
    else:
        driver.quit()
        return None


def classify_article(article_text, url, kws, exclude_kws):
    for exclude_kw in exclude_kws:
        if exclude_kw in article_text:
            return False, None
    if ('national-security' in url) or ('jerusalem' in url):
        return False, None
    for blm_kw in blm_kws:
        if blm_kw in article_text:
            return True, blm_kw
    return False, None


def count_articles(d):
    count = 0
    for date, articles in d.items():
        count += len(articles)
    return count


def main():

    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Make BLM keywords list')
    blm_kws, exclude_kws = make_blm_kw_list.main()


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Classify articles')

    kw_counter = defaultdict(int)
    blm_articles = {}
    n_articles = 0
    for article_src in article_srcs:
        with open(article_src, 'r') as f:
            articles = json.load(f)
        for date, days_articles in articles.items():
            blm_days_articles = []       
            for article in days_articles:
                n_articles += 1
                try:
                    article_comments_url = article['url'] + '#disqus_thread'
                    li = [article['title'], article['fulltext'], ' '.join(article['tags'])]
                    article_text = ' '.join(li).lower().strip()
                    is_blm, blm_kw = classify_article(article_text, article['url'], blm_kws, exclude_kws)
                    if is_blm == True:
                        blm_days_articles.append(article)
                        kw_counter[blm_kw] += 1
                except:
                    pass
            blm_articles[date] = blm_days_articles

    # kw_counter just a quick and dirty way to get an idea of what keywords are triggering blm classification
    print(kw_counter)

    # print classification summary statistics
    n_blm_articles = count_articles(blm_articles)
    fraction_classified_blm = round(n_blm_articles / n_articles, 2)
    print('\n%s articles classified as blm, a fraction of %s of %s total articles' % (n_blm_articles, fraction_classified_blm, n_articles))

    # remove dates that don't include any articles classified as blm / police brutality 
    blm_articles = {k:v for k, v in blm_articles.items() if len(v) > 0}


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Scrape comments')

    start = pd.Timestamp('2013-07-01')
    end = pd.Timestamp('2018-08-31')
    start, end
    try:
        driver.quit()
    except:
        pass

    counter = 0

    blm_articles_w_comments = {}
    for date, days_articles in blm_articles.items():
        print(date)
        # get comments beginning on desired start date
        if (pd.Timestamp(date) > start) & (pd.Timestamp(date) < end):
            days_articles_li = []
            for ix, article in enumerate(days_articles):
                comments_url = article['url'] + '#disqus_thread'
                # navigate to article url, skip if there is an exception
                article['comments'] = None

                # four tries and then bail, increase wait times each iteration
                for i in range(1, 4+1):
                    try:
                        if i == 1:
                            article['comments'] = get_iframe_text(comments_url)
                        else:
                            article['comments'] = get_iframe_text(comments_url, sleep=i*1, wait=2*i)
                        if article['comments'] != None:
                            break
                    except:
                        pass
                days_articles_li.append(article)  # append article to list of day's articles
                counter += 1  # track how many articles we've processed

            # build output dictionary that includes comments but is otherwise identical to input dictionary
            blm_articles_w_comments[date] = days_articles_li

            # save if, after end of day, number of articles exceeds 100

            if counter > 10:

                # build filename and define destination path
                min_date_str = str(min([pd.Timestamp(x) for x in blm_articles_w_comments.keys()]).date())
                max_date_str = str(max([pd.Timestamp(x) for x in blm_articles_w_comments.keys()]).date())
                fn = '_'.join([site, min_date_str, max_date_str]) + '.pkl'
                dst = os.path.join(blm_html_1pass_dir, fn)
                with open(dst, 'wb') as f:
                    pickle.dump(blm_articles_w_comments, f)

                # re-initialize counter and output dictionary
                counter = 0
                blm_articles_w_comments = {}

if __name__ == '__main__':
    main()
