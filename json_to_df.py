import argparse
import json
import os

import pandas as pd

from unidecode import unidecode
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def getSentiment(df, field, analyzer):
    l = lambda x: pd.Series(analyzer.polarity_scores(x))
    sent = df[field].apply(l)
    sent.columns = [field + '_sent_' + x for x in sent.columns]
    df = pd.concat([df, sent], axis=1)

    return df


def run(args_dict):
    #
    # Loop through raw UGB JSON files and pull out text and metadata
    # for analysis.
    #

    SOURCE = args_dict['source']
    DIR = args_dict['directory']
    verbose = args_dict['verbose']

    files = [file for file in os.listdir(DIR) if
                ('json' in file and SOURCE in file)]
    comments = []
    arts = []

    #
    # Process all articles and comments into lists of tuples
    #

    for file in files:
        file = open('{}/{}'.format(DIR, file), 'r')
        data = json.load(file)

        for date in data.keys():
            for i, article in enumerate(data[date]):
                art_id = '.'.join([date,str(i)])
                title = article['title']
                auth = article['author']
                art_cmts = article['parsed_comments']
                art_txt = article['fulltext']

                arts = arts + [(date,
                                art_id,
                                title,
                                auth,
                                len(art_cmts),
                                art_txt)]

                comments = comments + [(art_id,
                                        cmt['commenter_id'],
                                        cmt['comment_reply_to_id'],
                                        cmt['comment'],
                                        cmt['upvotes']) for cmt in art_cmts]

    #
    # Convert lists of tuples to DataFrames
    #

    comments = pd.DataFrame(comments)
    comments.columns = ['art_id',
                        'commenter',
                        'parent',
                        'comment_txt',
                        'upvotes']

    arts = pd.DataFrame(arts)
    arts.columns = ['date',
                    'art_id',
                    'art_title',
                    'art_author',
                    'art_comments',
                    'art_text']

    #
    # Transliterate Unicode characters to ASCII for more coherent and
    # predictable analyis later in R.
    #

    arts.art_text = arts.art_text.apply(lambda x: unidecode(x))
    comments.comment_txt = comments.comment_txt.apply(lambda x: unidecode(x))

    #
    # Perform VADER Sentiment Analysis on article titles, text, and comment text
    #

    analyzer = SentimentIntensityAnalyzer()

    arts = getSentiment(arts, 'art_title', analyzer)
    arts = getSentiment(arts, 'art_text', analyzer)

    comments = getSentiment(comments, 'comment_txt', analyzer)

    #
    # Save dataframes
    #

    arts.to_csv('{}/{}_articles.csv'.format(DIR, SOURCE))
    comments.to_csv('{}/{}_comments.csv'.format(DIR, SOURCE))

    #
    # Save text for training embeddings separately
    #

    corpus = pd.concat([arts.art_text, comments.comment_txt])
    corpus.to_csv('{}/{}_texts.csv'.format(DIR,SOURCE))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Conversion of scraped '
                        'articles and comments from JSON storage to CSV.')
    parser.add_argument('-d', '--directory', required=True,
                        help='Desired working directory')
    parser.add_argument('-s', '--source', required=True,
                        help='Name of the media source')
    parser.add_argument('-v', '--verbose', action="store_true",
                        help='Output progress reporting.')
    args_dict = vars(parser.parse_args())

    run(args_dict)

