# DARPA Understanding Group Biases (UGB) Disruptioneering Opportunity
## Introduction
Gallup's work - Strategic Applied Perception-Interpretation Research (SAPIR) - on behalf of the DARPA UGB opportunity will demonstrate new applications of natural language processing (NLP) techniques to the challenge of measuring the relative spread of cultural models/biases. SAPIR will generate insights to help analysts and decision-makers better understand how such biases affect humans' perceptions and interpretations of events. Specifically, SAPIR has scraped articles from a variety of news sources, along with associated comments, to provide a corpus through which to understand cultural biases.

Data for SAPIR are available by request to [Matt Hoover](matt_hoover@gallup.com).

## Setup
The majority of SAPIR is programmed in Python (3.x), with some modeling undertaken in R. Both are freely available for install. Python requirements are detailed in the `requirements.txt` file and should be installed prior to proceeding. Note, Gallup **highly recommends** the use of a virtual environment, at least for the Python portion, for code execution.

## Getting articles
The Python script, `get_data.py` utilizes the classes defined in `__init__.py` to scrape data from various news sources. *These scrapers are all functional as of 18 October 2018.* In the future, based on site architecture changes, the scrapers may need to be adjusted. This can be done via the `__init__.py` file; feel free to submit a pull request to the repository if you update a scraper class.

The call for data involves two required arguments: a site to scrape and a date range for which to run the scraper over. Currently, four scrapers are available for [Huffington Post](www.huffintonpost.com), [Breitbart News](www.breitbart.com), [The Guardian](www.guardian.com), and [The New York Post](www.nypost.com). Dates should be specified as YYYY-MM-DD. See below for an example call:

```
$ python get_data.py -s nyp -d 2015-07-01 2015-07-31
```

## Indexing via Elasticsearch
SAPIR takes advantage of Elasticsearch for one-time indexing and updating to allow fast querying of data. With the index of articles and comments, data for any range of topics can be queried and returned for analysis without having to load scraped content each time. This should save time and effort for individuals conducting analyses in the long term.

Articles and comments are indexed separately within Elasticsearch, but each is keyed with a URL. Therefore, if one queries articles using particular search terms and then wants to pull associated comments, one could use the URLs extracted from relevant articles to obtain comments. Putting the articles and comments together in an analytic program like Python or R is trivial from there.

To create the Elasticsearch index, use the `index_es.py` script. This takes three optional arguments: Elasticsearch host/port information (defaults to localhost on port 9200), an articles directory and desired index name for articles, and a comments directory and desired index name for comments. The `index_es.py` script assumes that data to be indexed were collected, structured, and keyed as specified within the `get_data.py` script. Some example calls are demonstrated below:

**To index articles (or comments) only**
```
$ python index_es.py -a data articles

$ python index_es.py -c data/comments comments
```

**To index articles and comments**
```
$ python index_es.py -a data articles -c data/comments comments
```

## Modeling
Work in progress

## Conclusion
This repository will continue to expand as addiitonal pieces of the SAPIR approach, including the natural language processing and hierarchical modeling of bias, are introduced through Gallup's continued work. If there are questions, please reach out to [Matt Hoover](matt_hoover@gallup.com) for resolution.
