import requests
import re
import sys

import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime


class Scraper:
    def __init__(self):
        self.header = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:61.0) Gecko/20100101 Firefox/61.0'
        }
        self.timeout = 10

    def scrape(self, article):
        d = requests.get('{}/{}'.format(self.site, article), headers=self.header)
        return BeautifulSoup(d.text, 'html.parser')

    def extract_attribute(self, text, attribute, listtype=False):
        if listtype:
            try:
                return [x['content'] for x in text if attribute in x['property']]
            except IndexError:
                return None
        else:
            try:
                return [x['content'] for x in text if attribute in x['property']][0]
            except IndexError:
                return None

    def format_dates(self, beg, end):
        dr = pd.date_range(beg, end)
        return [datetime.strftime(x, '%Y-%m-%d') for x in dr]

    def gather_articles(self, url, dnum, anum, dtot, atot):
        print('Gathering article {} of {} for day {} of {}...'
              .format(anum, atot, dnum, dtot))
        if 'iaf.tv' not in url:
            d = requests.get(url, headers=self.header)
            return BeautifulSoup(d.text, 'html.parser')

    def get_date_components(self, date):
        yr = datetime.strptime(date, '%Y-%m-%d').year
        mt = datetime.strptime(date, '%Y-%m-%d').month
        dy = datetime.strptime(date, '%Y-%m-%d').day
        return yr, mt, dy

class Breitbart(Scraper):
    def __init__(self):
        self.site = 'https://www.breitbart.com'
        super().__init__()

    def gather_archive(self, date):
        yr, mth, day = self.get_date_components(date)
        links = []

        for topic in ['big-government', 'big-journalism', 'news']:
            d = requests.get('{}/{}/{}/{}/{}'.format(self.site, topic, yr, mth,
                                                     day), headers=self.header)
            soup = BeautifulSoup(d.text, 'html.parser')
            tmp = soup.find_all('a', attrs={'class': 'tco'})
            links += tmp
        return [link['href'] for link in links]

    @staticmethod
    def get_main_text(article):
        texts = article.find_all('p', attrs={'class': None})
        return ' '.join([text.text for text in texts])

    def get_metadata(self, article):
        metadata_text = article.select('meta[property]')
        title = self.extract_attribute(metadata_text, 'og:title')
        edition = self.extract_attribute(metadata_text, 'og:locale')
        tags = self.extract_attribute(metadata_text, 'article:tag', listtype=True)
        url = self.extract_attribute(metadata_text, 'og:url')
        try:
            isAnyContributor = self.extract_attribute(metadata_text, 'article:section')
        except IndexError:
            isAnyContributor = None
        try:
            author = article.select('address[data-aname]')[0]['data-aname']
        except IndexError:
            author = None

        return {
            'title': title,
            'author': author,
            'edition': edition,
            'isAnyContributor': isAnyContributor,
            'tags': tags,
            'url': url,
        }

class Guardian(Scraper):
    def __init__(self):
        self.site = 'https://www.theguardian.com'
        self.month_converter = {
            1: 'jan',
            2: 'feb',
            3: 'mar',
            4: 'apr',
            5: 'may',
            6: 'jun',
            7: 'jul',
            8: 'aug',
            9: 'sep',
            10: 'oct',
            11: 'nov',
            12: 'dec',
        }
        super().__init__()

    def gather_archive(self, date):
        yr, mth, day = self.get_date_components(date)
        mth = self.month_converter[mth]
        if len(str(day))==1:
            day = '0'+str(day)
        links = []

        for topic in ['world', 'us-news']:
            d = requests.get('{}/{}/{}/{}/{}'.format(self.site, topic, yr, mth, day), headers=self.header)
            soup = BeautifulSoup(d.text, 'html.parser')
            tmp = soup.find_all('a', attrs={'class': 'fc-item__link',
                                            'data-link-name': 'article'})
            links += tmp
        return [link['href'] for link in links]

    @staticmethod
    def get_main_text(article):
        texts = article.find_all('div', attrs={
            'data-test-id':  'article-review-body',
        })
        if len(texts)>0:
            return ' '.join([text.text for text in texts])
        else:
            texts = article.find_all('p')
            return ' '.join([text.text for text in texts])

    def get_metadata(self, article):
        metadata_text = article.select('meta[property]')
        title = self.extract_attribute(metadata_text, 'og:title')
        edition = self.extract_attribute(metadata_text, 'article:section')
        tags = self.extract_attribute(metadata_text, 'article:tag', listtype=True)
        url = self.extract_attribute(metadata_text, 'og:url')
        isAnyContributor = self.extract_attribute(metadata_text, 'og:site_name')
        try:
            author = [x['content'] for x in article.select('meta[name]') if
                      x['name'] == 'author'][0]
        except IndexError:
            author = None

        return {
            'title': title,
            'author': author,
            'edition': edition,
            'isAnyContributor': isAnyContributor,
            'tags': tags,
            'url': url,
        }

class HuffPost(Scraper):
    def __init__(self):
        self.site = 'https://www.huffingtonpost.com'
        super().__init__()

    def gather_archive(self, date):
        d = requests.get('{}/archive/{}'.format(self.site, date), headers=self.header)
        soup = BeautifulSoup(d.text, 'html.parser')
        links = soup.find_all('a', attrs={'class': 'card__link yr-card-headline'})
        return [link['href'] for link in links]

    @staticmethod
    def get_main_text(article):
        texts = article.find_all('div', attrs={
            'class': 'content-list-component yr-content-list-text text'
        })
        if len(texts)>0:
            return ' '.join([text.text for text in texts])
        else:
            texts = article.find_all('p')
            return ' '.join([text.text for text in texts])

    def get_metadata(self, article):
        metadata = {}
        try:
            metadata_text = [x for x in article.find_all('script') if
                             'isAnyContributor' in x.text][0].text
            for term in ['title', 'author', 'edition', 'isAnyContributor', 'tags', 'url']:
                try:
                    ans = re.search('(?<={}:)(.*)'.format(term),
                                    metadata_text).group(0)
                    ans = re.sub('"|,', '', ans.strip())
                    metadata.update({term: ans})
                except AttributeError:
                    pass
        except IndexError:
            metadata.update({})
        return metadata

class NYPost(Scraper):
    def __init__(self):
        self.site = 'https://nypost.com'
        super().__init__()

    def gather_archive(self, date):
        yr, mth, day = self.get_date_components(date)

        d = requests.get('{}/{}/{}/{}'.format(self.site, yr, mth, day),
                         headers=self.header)
        soup = BeautifulSoup(d.text, 'html.parser')
        links = soup.select('h3[class]')
        print('Gathering index for {}'.format(date))
        try:
            return [link.find('a')['href'] for link in links]
        except TypeError:
            return [d.url]

    @staticmethod
    def get_main_text(article):
        texts = article.find_all('div', attrs={
            'class': 'entry-content entry-content-read-more'
        })
        if len(texts)>0:
            return ' '.join([text.text for text in texts])
        else:
            texts = article.find_all('p')
            return ' '.join([text.text for text in texts])

    def get_metadata(self, article):
        metadata_text = article.select('meta[property]')
        authors = article.find_all('p', attrs={'class': 'byline'})

        title = self.extract_attribute(metadata_text, 'og:title')
        edition = self.extract_attribute(metadata_text, 'og:locale')
        tags = [x['content'] for x in article.select('meta[name]') if
                'news_keywords' in x['name']]
        url = self.extract_attribute(metadata_text, 'og:url')
        isAnyContributor = self.extract_attribute(metadata_text, 'og:site_name')
        try:
            if authors[0].find_all('a'):
                author = [x.text for x in authors[0].find_all('a')]
            else:
                author = [x.text for x in authors]
        except IndexError:
            author = None

        return {
            'title': title,
            'author': author,
            'edition': edition,
            'isAnyContributor': isAnyContributor,
            'tags': tags,
            'url': url,
        }
