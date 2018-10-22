# DARPA Understanding Group Biases (UGB) Disruptioneering Opportunity
## Introduction
Gallup's work - Strategic Applied Perception-Interpretation Research (SAPIR) - on behalf of the DARPA UGB opportunity will demonstrate new applications of natural language processing (NLP) techniques to the challenge of measuring the relative spread of cultural models/biases. SAPIR will generate insights to help analysts and decision-makers better understand how such biases affect humans' perceptions and interpretations of events. Specifically, SAPIR has scraped articles from a variety of news sources, along with associated comments, to provide a corpus through which to understand cultural biases.

Data for SAPIR are available by request to Matt Hoover (<matt_hoover@gallup.com>).

## Setup
The majority of SAPIR is programmed in Python (3.x), with some modeling undertaken in R. Both are freely available for install. Python requirements are detailed in the `requirements.txt` file and should be installed prior to proceeding. Note, Gallup **highly recommends** the use of a virtual environment, at least for the Python portion, for code execution.

## Data acquisition
### Getting articles
The Python script, `get_data.py` utilizes the classes defined in `__init__.py` to scrape data from various news sources. *These scrapers are all functional as of 18 October 2018.* In the future, based on site architecture changes, the scrapers may need to be adjusted. This can be done via the `__init__.py` file; feel free to submit a pull request to the repository if you update a scraper class.

The call for data involves two required arguments: a site to scrape and a date range for which to run the scraper over. Currently, four scrapers are available for [Huffington Post](https://www.huffintonpost.com), [Breitbart News](https://www.breitbart.com), [The Guardian](https://www.guardian.com), and [The New York Post](https://www.nypost.com). Dates should be specified as YYYY-MM-DD. See below for an example call:

```
$ python get_data.py -s nyp -d 2015-07-01 2015-07-31
```

### Getting comments
The `make_comments.py` is currently configured to obtain and process comments for Breitbart and Guardian articles for a selected topic.

Dependencies:
* This script depends on the outputs from the `get_data.py` module, which are used as inputs to obtain the comments
* We use the Google CustomSearch API to select articles related to a selected topic, and provide instructions for obtaining credentials below:
  * Create a [free Google account](https://cloud.google.com/billing/docs/how-to/manage-billing-account)
  * Navigate to the [Google CustomSearch page](https://cse.google.com/cse/) and [follow the instructions](https://developers.google.com/custom-search/docs/tutorial/creatingcse) to create a custom API
  * On the [Google CustomSearch page](https://cse.google.com/cse/), indicate your topic ("Search engine keywords" text box), the sites you'd like to search ("Sites to search" table), and under the "Restrict Pages using Schema.org Types" input "NewsArticle" so that we can get search data in the proper format
  * Create a 'config.py' file in the 'src' directory; refer to the config_example.py for an illustration
  * Input the Google CustomSearch cx and developerKey variables, as strings, into the config.py file you created.

Run `make_comments.py` using the terminal command `python make_comments.py`, which imports modules from the 'src' directory and does the following:
* Breitbart comment data
  * Make BLM keywords for Breitbart article classification
  * Get comments
  * Process comments
* Guardian comment data
  * Classify Guardian articles
  * Get Guardian comments
  * Process Guardian comments

Outputs are saved in the 'data' directory, and these are used as inputs for the modeling routines.

### Indexing via Elasticsearch
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

## Data modeling
Work in progress

## Conclusion
This repository will continue to expand as addiitonal pieces of the SAPIR approach, including the natural language processing and hierarchical modeling of bias, are introduced through Gallup's continued work. If there are questions, please reach out to Matt Hoover (<matt_hoover@gallup.com>) for resolution.
