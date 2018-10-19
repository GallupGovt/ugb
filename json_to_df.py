
import json
import os


import pandas as pd


from unidecode import unidecode
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# 
# Loop through raw UGB JSON files and pull out texts for analysis in R with
# tex2vec package.
# 

DIR = 'C:/Users/ben_ryan/Documents/DARPA UGB'
bfiles = [file for file in os.listdir(DIR) if ('json' in file and 'breitbart' in file)]
bcomments = []
barts = []

#
# Process all comments into one DataFrame
# 

for file in bfiles:
    file = open('{}/{}'.format(DIR, file), 'r')
    data = json.load(file)

    for date in data.keys():
        for i, article in enumerate(data[date]):
            title = article['title']
            author = article['author']
            art_id = '.'.join([date,str(i)])

            bcomments = bcomments + [(date, 
                                      title,
                                      author,
                                      art_id,
                                      comment['commenter'], 
                                      comment['parent_commenter'], 
                                      comment['comment'], 
                                      comment['upvotes']) for comment in article['parsed_comments']]

bc = pd.DataFrame(bcomments)
bc.columns = ['date',
              'art_title',
              'art_author',
              'art_id',
              'commenter',
              'parent',
              'comment_txt',
              'upvotes']

#
# Process all articles into one DataFrame
# 

for file in bfiles:
    file = open('{}/{}'.format(DIR, file), 'r')
    data = json.load(file)

    for date in data.keys():
            barts = barts + [(date, 
                              '.'.join([date,str(i)]),
                              article['title'], 
                              article['author'],
                              len(article['parsed_comments']),
                              article['fulltext']) for i, article in enumerate(data[date])]

barts = pd.DataFrame(barts)
barts.columns = ['date','art_id','art_title','art_author','art_comments','art_text']

#
# Transliterate Unicode characters to ASCII for more coherent and
# predictable analyis later in R. 
#

barts.art_text = barts.art_text.apply(lambda x: unidecode(x))
bc.comment_txt = bc.comment_txt.apply(lambda x: unidecode(x))

#
# Perform VADER Sentiment Analysis on article titles, text, and comment text
# 

analyzer = SentimentIntensityAnalyzer()

title_sents = barts.art_title.apply(lambda x: pd.Series(analyzer.polarity_scores(x)))
title_sents.columns = ["title_sent_"+x for x in title_sents.columns]

art_sents = barts.art_text.apply(lambda x: pd.Series(analyzer.polarity_scores(x)))
art_sents.columns = ["art_sent_"+x for x in art_sents.columns]

barts = pd.concat([barts, title_sents, art_sents], axis=1)


comm_sents = bc.comment_txt.apply(lambda x: pd.Series(analyzer.polarity_scores(x)))
comm_sents.columns = ["comm_sent_"+x for x in comm_sents.columns]

bc = pd.concat([bc, comm_sents], axis=1)

#
# Save dataframes
# 

barts.to_csv('{}/breitbart_articles.csv'.format(DIR))
bc.to_csv('{}/breitbart_comments.csv'.format(DIR))

#
# Save text for training embeddings separately
# 

b_corpus = pd.concat([barts.art_text, bc.comment_txt])
b_corpus.to_csv('{}/breitbart_texts.csv'.format(DIR))


