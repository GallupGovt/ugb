#!/usr/local/Cellar/python/3.6.5/bin
# -*- coding: utf-8 -*-
import argparse
import json
import os
import requests

from elasticsearch import Elasticsearch


def run_indexing(es, directory, index, article=True):
    i = 1
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            source = filename.split('_')[0]
            with open('{}/{}'.format(directory, filename), 'r') as f:
                jdata = json.load(f)
            for key in jdata.keys():
                for entry in jdata[key]:
                    if article:
                        entry.update({
                            'date': key,
                            'source': source,
                        })
                        es.index(index=index, ignore=400, doc_type='article',
                                 id=i, body=entry)
                        i += 1
                    else:
                        for comment in entry['parsed_comments']:
                            try:
                                comment.update({
                                    'date': key,
                                    'source': source,
                                    'url': entry['url'],
                                })
                                es.index(index=index, ignore=400,
                                         doc_type='comment', id=i, body=comment)
                            except AttributeError:
                                pass
                            i += 1

    return None


def run(args_dict):
    es = Elasticsearch(
        [
            {
                'host': args_dict['es'][0],
                'port': args_dict['es'][1],
            },
        ],
    )

    if args_dict['articles']:
        run_indexing(es, args_dict['articles'][0], args_dict['articles'][1],
                     True)
    if args_dict['comments']:
        run_indexing(es, args_dict['comments'][0], args_dict['comments'][1],
                     False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Index data in ES.')
    parser.add_argument('-a', '--articles', required=False, nargs=2,
                        help='Path to data and index name, in order.')
    parser.add_argument('-c', '--comments', required=False, nargs=2,
                        help='Path to comments and index name, in order.')
    parser.add_argument('-e', '--es', required=False, nargs=2,
                        default=['localhost', '9200'], help='Optional host and '
                        'port for ES instance; defaults to localhost on port '
                        '9200 per ES standards.')
    args_dict = vars(parser.parse_args())

    run(args_dict)
