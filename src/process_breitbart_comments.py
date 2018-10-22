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




class ArticlePosts:
    """Process and organize comments data for one article."""
    

    def __init__(self, html):
        if html == None:
            raise ValueError('This article has no comments')
        if type(html) != str:
            raise TypeError('HTML must be a string')
        self.html = html
        self.begin_splitters = ['Privacy Policy−+']
        self.end_splitters = ['Also on Breitbart News Network', '•Reply•Share ›TwitterFacebookLoad more commentsAlso on Breitbart News Network']
        self.post_splitter = '•Reply•Share ›TwitterFacebook−+'
        self.replacements = [{'pattern': '•Reply•Share ›TwitterFacebook−+', 'replacement': '', 'regex': False}
                            ,{'pattern': '(• \d )(years ago)', 'replacement': '', 'regex': True}
                            ,{'pattern': '(see more)\d+', 'replacement': '', 'regex': True}
                            ,{'pattern': ' +', 'replacement': ' ', 'regex': True}
                            ,{'pattern': 'SubscribeDisqus\' Privacy PolicyPrivacy PolicyPrivacy', 'replacement': '', 'regex': False}]
        
    def clean_html(self):
        """Chop off extraneous parts of page code."""
        self.cleaned_html = self.html.strip()
        for begin_splitter in self.begin_splitters:
            self.cleaned_html = self.cleaned_html.split(begin_splitter)[-1]
        for end_splitter in self.end_splitters:
            self.cleaned_html = self.cleaned_html.split(end_splitter)[0]
        self.cleaned_html = self.cleaned_html.strip()
        return self.cleaned_html
    
    def make_unparsed_comments(self, replacements):
        """Generate string of concatenated comments for one article."""
        if not hasattr(self, 'cleaned_html'):
            self.cleaned_html = self.clean_html()
            
        self.basic_comments = self.cleaned_html
        for d in self.replacements:
            if d['regex']:
                self.basic_comments = re.sub(d['pattern'], d['replacement'], self.basic_comments)
            else:
                self.basic_comments = self.basic_comments.replace(d['pattern'], d['replacement'])
        return self.basic_comments
    

    post_splitter = '•Reply•Share ›TwitterFacebook−+'
    def separate_comments(self):
        """Create list of posts using post_splitter."""
        if not hasattr(self, 'cleaned_html'):
            self.cleaned_html = self.clean_html()
        
        self.separated_comments = self.cleaned_html.split(self.post_splitter)
        return self.separated_comments
    
    def get_comment_data(self, comment):
        """Obtain commenter, parent_commenter, comment, and upvotes from comment.
        Helper function used with assemble_article_comments."""
        # remove double spaces but not triple ones; we use triple spaces to split commenter and parent_commenter
        pattern = '(?<! ) {2}(?! )'
        comment = re.sub(pattern, ' ', comment).strip()  # also strip leading and trailing spaces

        # get names
        ix = re.search('•', comment).span()[-1]
        names = [x.strip() for x in (comment[:ix]).strip().strip('•').split('  ')]
        try:
            commenter, parent_commenter = names
        except:
            commenter, parent_commenter = names[0], ''

        # handle deleted comments
        pattern = 'This comment was deleted.−+−+'
        commenter = commenter.replace(pattern, '').strip()
        
        # get post and upvotes
        comment_upvotes = comment[ix:].split('ago')[-1].strip(' ')
        ix = re.search('(see more)\w+', comment_upvotes)  # redefine ix as index that separates post message from post upvotes
        clean_comment, upvotes = comment_upvotes[:ix.span()[0]], comment_upvotes[ix.span()[0]:].replace('see more', '')

        # build dictionary
        d = dict(zip(  ['commenter', 'parent_commenter', 'comment', 'upvotes']
                     , [commenter, parent_commenter.strip(), clean_comment.strip(), upvotes.strip()]))

        return d
    
    def make_parsed_comments(self):
        """Iterate over each comment and extract data from each comment using get_comment_data() function."""
        if not hasattr(self, 'separated_comments'):
            self.separated_comments = self.separate_comments()
        
        # build comments list of dictionaries, one dictionary for each article
        self.comments = []
        for self.separated_comment in self.separated_comments:
            try:
                comment_data = self.get_comment_data(self.separated_comment)
                self.comments.append(comment_data)
            except Exception as e:
                pass
        return self.comments


def save_outputs(d, dst_dir, site, file_format='json', write_mode='w'):
    """Build filename and define destination path and save outputs."""
    
    
    min_date_str = str(min([pd.Timestamp(x) for x in d.keys()]).date())
    max_date_str = str(max([pd.Timestamp(x) for x in d.keys()]).date())
    fn = '_'.join([site, min_date_str, max_date_str]) + '.' + file_format
    dst = os.path.join(dst_dir, fn)
    with open(dst, write_mode) as f:
        if (file_format == 'json') & (write_mode =='w'):
            json.dump(d, f)
        elif (file_format == 'pkl') & (write_mode == 'wb'):
            pickle.dump(d, f)
        else:
            raise ValueError("File format or write mode incorrect.\nOptions are 1) 'json', 'w' and 2) 'pkl', 'wb'")    


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# DEFINE INPUTS

site = 'breitbart'
dst_dir = os.path.join(utilities.blm_processed_parsed_dir, '2nd_iteration')
utilities.mkdir(dst_dir)  # make dst dir if it doesn't exist


def main():
            
    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    print('Parse comments')

    # combine scraped blm data
    blm_srcs = utilities.get_files(utilities.blm_html_1pass_dir) + utilities.get_files(utilities.blm_html_2pass_dir)
    blm_srcs = [x for x in blm_srcs if site in x]
    blm = utilities.combine_dicts(blm_srcs)

    # sort by date
    blm_sorted = {}
    for k in sorted(blm.keys()):
        blm_sorted_v = copy.deepcopy(blm[k])
        blm_sorted[k] = blm_sorted_v


    article_counter = 0
    # iterate over websites
    counter = 0
    # for each website, iterate over intermediate pickle files
    blm_comments = {}

    # for each loaded dict, iterate over each day's articles
    for date, days_articles in blm_sorted.items():
        days_articles_li = []
        # for each article, get cleaned comments
        for ix, article in enumerate(days_articles):
                article_copy = copy.deepcopy(article)  # copy so when we change article we don't change blm_sorted article
                comments = article_copy['comments']
                # exclude articles that don't have comments
                if type(comments) == str:
                    soup = bs(comments)
                    ap = ArticlePosts(comments)
                    article_copy['unparsed_comments'] = ap.make_unparsed_comments(ap.replacements)
                    article_copy['parsed_comments'] = ap.make_parsed_comments()
                    article_copy['raw_comments'] = article_copy.pop('comments')
                    days_articles_li.append(article_copy)
                    counter += 1
                    article_counter += 1

        # only add day's articles if there were any articles for that day
        if len(days_articles_li) > 0:
            blm_comments[date] = days_articles_li

        # at the end of the day, if counter greater than x, save and reinitialize dictionary and counter
        if counter >= 1000:
            save_outputs(blm_comments, dst_dir, site)
            # re-initialize dictionary and counter
            blm_comments = {}
            counter = 0

    # save remainders
    if len(blm_comments) > 0:
        save_outputs(blm_comments, dst_dir, site)

    print('Total articles with comments = %s' % article_counter)


if __name__ == '__main__':
    main()