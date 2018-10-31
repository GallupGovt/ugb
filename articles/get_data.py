#!/usr/local/Cellar/python/3.6.5/bin
# -*- coding: utf-8 -*-
import argparse
import json
import sys

from datetime import datetime

from ugb.articles import Scraper, Breitbart, Guardian, HuffPost, NYPost


def choose_class(arg):
    if arg in 'breitbart':
        return Breitbart()
    elif arg in 'guardian':
        return Guardian()
    elif arg in 'huffpost':
        return HuffPost()
    elif arg in 'nyp':
        return NYPost()
    else:
        sys.exit('That news source is not defined; try again.')


def date_formatter(x):
    try:
        return datetime.strptime(x, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError('Not a valid date.')


def run(args_dict):
    # instantiate class
    driver = choose_class(args_dict['site'])

    # run operation(s)
    date_range = driver.format_dates(args_dict['dates'][0],
                                     args_dict['dates'][1])
    article_index = [driver.gather_archive(date) for date in date_range]

    articles = [[driver.gather_articles(url, i, j, len(article_index), len(day)) for
                j, url in enumerate(day)] for i, day in enumerate(article_index)]
    print('Finished gathering articles...')

    # detour for the ny post...
    if 'nyp' in args_dict['site']:
        articles = [[content for content in article if content] for article in
                    articles]

    text = [[driver.get_main_text(url) for url in day] for day in articles]
    print('Finished gathering text...')
    metadata = [[driver.get_metadata(url) for url in day] for day in articles]
    print('Finished gathering metadata...')

    # save data
    [[m.update({'fulltext': t}) for m, t in zip(md, tx)] for md, tx in
     zip(metadata, text)]
    data = {date: md for date, md in zip(date_range, metadata)}

    beg = datetime.strftime(args_dict['dates'][0], '%Y-%m-%d')
    end = datetime.strftime(args_dict['dates'][1], '%Y-%m-%d')
    with open('data/{}_{}_{}.json'.format(args_dict['site'], beg, end), 'w') as f:
        json.dump(data, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape data from news sites.')
    parser.add_argument('-s', '--site', required=True, choices=['breitbart',
                        'guardian', 'huffpost', 'nyp'], help='Website to '
                        'scrape for data.')
    parser.add_argument('-d', '--dates', nargs=2, required=True,
                        type=date_formatter, help='Date inputs, start and end, '
                        'in YYYY-MM-DD format.')

    args_dict = vars(parser.parse_args())

    run(args_dict)
