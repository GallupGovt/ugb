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

## Featurization
### Python pre-processing
Pre-processing on the scraped data is run in Python, using base modules and managing file input/output with `json` and `pandas` modules. In addition, the `unidecode` and `vaderSentiment` modules are used to clean text and perform sentiment analysis, respectively. 

Scraped article and comment data is initially stored in JSON files, and after pre-processing are output into CSV files for further analysis and feature extraction in R. To process articles and comments for a particular source, use the `json_to_df.py` script. This script takes three options: the directory housing the scraped JSON files, the name of the source (e.g., "breitbart" or "guardian"), and a "verbose" flag to control whether progress reports are output during execution. The script assumes that all JSON files in the given directory with the "source" string in the filename are to be included. The script loops through a list of files matching that description and compiles a Pandas DataFrame with each row representing one comment, and columns for comment features and related article features. Once the raw data has been refactored from JSON into a DataFrame, the script transliterates text fields into ASCII, and performs sentiment analysis on them, producing a set of four real numbers {pos: n, neu: n, neg: n, compound: n} characterizing the sentiment polarity and intensity of each text field. 

Finally, the script saves DataFrames representing article features, comment features, and a combined corpus of article and comment text to disk as CSV files. An example call is demonstrated below:

**To process articles and comments from Breitbart with verbose output**
```
$ python json_to_df.py -d /usr/data -s breitbart -v
```

### R featurization
Further featurization and analysis is run in R, primarily using `data.table`, `text2vec`, and `quanteda` packages. GloVe word embeddings are trained on our text corpus, mimicking the original Stanford approach in our parameters and methods at every step; optionally, these can be loaded from a pre-trained file. Bias themes are computed, currently covering "gender," "race" and "authoritarianism" themes, and scores for all text fields are computed for each. Finally, comments are clustered on the weighted average of their word embeddings to identify "communities" of commenters differentiated by word usage patterns. 

To execute this featurization, use the `get_features.R` script. This script is also run from the commandline using Rscript, and takes several arguments: the directory containing the source datasets produced by the python pre-processing, the name of the file with the articles data, the name of the file with the comments data, the name of the file with the text corpus, the name of the source being analyzed, and optionally a file with pre-trained word embeddings and a flag for verbose output.  

The `get_features.R` script sources three other R files: `clustering.R`, `glove_analysis.R`, and `bias_themes_analysis.R`. These load functions for performing automated k-means cluster analysis, GloVe featurization and analysis, and functions and word sets for constructing bias theme components, respectively, which should all reside in the same directory as the main script. After loading the data and setting up parallel processing resources, the script either loads pre-trained word embeddings or uses the `quanteda` `tokens()`, `dfm()` and `fcm()` functions to tokenize and produce a feature-co-occurence matrix (FCM) from the text corpus. This model is saved to the working directory at that time for later re-use as desired.

Once the GloVe model is prepared, article titles, text, and comments text are converted to weighted averages of their word embeddings. Bias theme component scores are derived similarly, taking the weighted average of the cosine similarity of all terms in a text field with each bias component vector. Sentiment scores and metadata for articles and comments (such as author, parent comment author, upvotes, and number of comments per article) are also merged in from the source datasets. 

Finally, comments are assigned to clusters using k-means clustering, with values for k from 2 to 15 tested and performance rated as the between-sum-of-squares error divided by the total-sum-of-squares error. The "best fit" cluster is selected automatically based on an “elbow graph” of these performance values, defining the "elbow" point as having the maximum Euclidean distance from a straight line drawn between the points [1,0] and [15,(performance of clustering with k=15)].

The resulting combined feature set with comment cluster assignments added is saved in the working directory as `$SOURCE_combined_features.csv`. An example call is demonstrated below:


**To process articles and comments from Breitbart with verbose output**
```
$ Rscript get_features.R -d /usr/data -s breitbart -a articles.csv -c comments.csv -t text_corpus.csv -w embeddings_model.txt -v
```

## Modeling
There are two key processes for modeling, both utilizing R. The first reads in the fully featurized data, simulates a user-specificed number of bias scores, and then saves a modeling-ready dataset to disk. This process is run *by news source* and will need to be executed for each news source that is sought for modeling.

The script itself, `create_bias.r` is in the `hlm` folder within this repository. It is meant to be a command-line executed script with three arguments.
* Argument 1: Path/name of the featurized datset to read in
* Argument 2: Path/name of the modeling-ready data to write out
* Argument 3: Path/name of the metadata variables associated with the simulated bias scores that map to the modeling-ready data; this is for diagnostic purposes to identify the random values used in each simulation if needed later on

To execute, run the following:
```
$ Rscript hlm/create_bias.r guardian_combined_features_v2.csv guardian_modeling_data.csv guardian_modeling_metadata.csv
```

The other piece of the modeling work is running the actual hierarchical linear models (HLMs). This is accomplished with the `hlm/hlm.r` script. This script reads in a variable number of modeling-ready datasets generated by the `hlm/create_bias.r` script and accepts a final parameter for the metric of interest (currently, gender, race, or authoritarianism (note, however, due to legacy code, authoritarianism should be called with the word 'power' instead)).

The script reads in the various datasets, identifies their source, combines them, identifies the variables associated with the metric of interest, and then simulates over all outcomes. Once complete, the script will produce two diagnostic plots that are written to disk as PDFs.

To execute, use the following:
```
$ Rscript hlm/hlm.r hlm/breitbart_modeling_data.csv hlm/guardian_modeling_data.csv race
```

## Conclusion
This repository will continue to expand as addiitonal pieces of the SAPIR approach, including the natural language processing and hierarchical modeling of bias, are introduced through Gallup's continued work. If there are questions, please reach out to Matt Hoover (<matt_hoover@gallup.com>) for resolution.
