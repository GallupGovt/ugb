# coding: utf-8
import inputs
import pandas as pd
import numpy as np
import os
import sys
import string
import re
import glob
import urllib
import datetime
import multiprocessing
import inspect
import pymysql.cursors
import pymysql
import re
import collections
import seaborn as sns
import matplotlib.pyplot as plt
import tldextract
import json
import pickle
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import warnings
warnings.simplefilter(action='ignore', category=Warning)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# DIRECTORIES

data_dir = inputs.abs_path_data_dir
blm_dir = os.path.join(data_dir, 'BLM')
tools_dir = os.path.join(os.path.dirname( __file__ ), 'tools')

blm_html_dir = os.path.join(blm_dir, 'HTML')
blm_html_1pass_dir = os.path.join(blm_html_dir, 'First_Pass')
blm_html_2pass_dir = os.path.join(blm_html_dir, 'Second_Pass')

blm_processed_dir = os.path.join(blm_dir, 'PROCESSED')
blm_processed_parsed_dir = os.path.join(blm_processed_dir, 'PARSED')
blm_processed_unparsed_dir = os.path.join(blm_processed_dir, 'UNPARSED')

blm_external_dir = os.path.join(blm_dir, 'z_External')


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# FILE MANAGEMENT FUNCTIONS

def get_files(_dir, extensions=None):
    """Retrieve paths for specified directory and extensions."""
    if extensions==None:
        paths = [glob.glob(os.path.join(_dir, '*.' + x)) for x in ['csv', 'xlsx', 'pickle', 'pkl', 'xls']]
        
            
    else:
        if type(extensions) != list:
            raise TypeError('Extensions must be input as a list')
        else:
            paths = [glob.glob(os.path.join(_dir, '*.' + x)) for x in extensions]
            if '' in extensions:
                paths += [glob.glob(os.path.join(_dir, '*' + x)) for x in extensions]
    paths = [item for sublist in paths for item in sublist if len(sublist) > 0 ]
    paths = [x for x in paths if '~' not in x]
    return paths


def mkdir(directory):
    """Make a directory if it doesn't already exist."""
    if not os.path.exists(directory):
        print('Make directory %s' % directory)
        os.makedirs(directory)
    else:
        print('Directory %s already exists' % directory)

        
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# MAKE ALL DIRECTORIES IF THEY DON'T EXIST
dirs = [ data_dir, blm_dir, tools_dir, blm_html_dir, blm_html_1pass_dir
        ,blm_html_2pass_dir, blm_processed_dir, blm_processed_parsed_dir
        ,blm_processed_unparsed_dir, blm_external_dir]

def make_data_dirs(dirs=dirs):
    """"Make data directories if they don\'t exist."""
    for a_dir in dirs:
        mkdir(a_dir)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# GET CHROMEDRIVERS AND SELECT PLATFORM-APPROPRIATE CHROMEDRIVER

def get_chromedrivers(tools_dir):
    """Download zipped chromedrivers for Linux, Mac, and Windows platforms and unzip."""
    linux_chromedriver_url = 'https://chromedriver.storage.googleapis.com/2.43/chromedriver_linux64.zip'
    mac_chromedriver_url = 'https://chromedriver.storage.googleapis.com/2.43/chromedriver_mac64.zip'
    windows_chromedriver_url = 'https://chromedriver.storage.googleapis.com/2.43/chromedriver_win32.zip'

    d = {'linux': linux_chromedriver_url, 'mac': mac_chromedriver_url, 'windows': windows_chromedriver_url}

    for op_sys, chromedriver_url in d.items():
        chromedriver_fn = os.path.basename(chromedriver_url)
        chromedriver_zip_path = os.path.join(tools_dir, chromedriver_fn)
        chromedriver_file = urllib.request.URLopener()
        chromedriver_file.retrieve(chromedriver_url, chromedriver_zip_path)
        zip_ref = zipfile.ZipFile(chromedriver_zip_path, 'r')
        op_sys_dir = os.path.join(tools_dir, op_sys)
        mkdir(op_sys_dir)
        zip_ref.extractall(op_sys_dir)    
        zip_ref.close()

    zip_files_to_remove = get_files(tools_dir, extensions=['zip'])
    for zip_file_to_remove in zip_files_to_remove:
        os.remove(zip_file_to_remove)

# determine operating system to select appropriate chromedriver
op_syss = {'win': 'windows', 'linux': 'linux', 'darwin': 'mac'}
[mkdir(os.path.join(tools_dir, x)) for x in list(op_syss.values())]
this_op_sys = sys.platform
this_op_sys_alias = None
for op_sys, op_sys_alias in op_syss.items():
    if op_sys in this_op_sys:
        this_op_sys_alias = op_sys_alias
if this_op_sys_alias is None:
    raise Exception('Unable to map operating system to Windows, Linux, or Mac OS\'s')
exts = {'windows': 'exe', 'mac': '', 'linux': ''}
this_chromedriver_ext = exts[this_op_sys_alias]

try:
    chromedriver_path = get_files(os.path.join(tools_dir, this_op_sys_alias), extensions=[this_chromedriver_ext])[0]
except IndexError:
    get_chromedrivers(tools_dir)
    chromedriver_path = get_files(os.path.join(tools_dir, this_op_sys_alias), extensions=[this_chromedriver_ext])[0]



# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# GENERIC FUNCTIONS



def flatten(li):
    return [item for sublist in li for item in sublist]


def instantiate_driver(url, wait=10, driver_path=r'G:\Strengths_Reporting\code\src\tools\chromedriver.exe', headless=False):
    """"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
    driver.get(url)
    driver.maximize_window()
    driver.implicitly_wait(wait)
    return driver


def count_articles(d):
    count = 0
    for date, articles in d.items():
        count += len(articles)
    return count


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


def combine_dicts(srcs):
    """Combine dictionaries saved as pickle or json files.
    Subsequent dictionaries with overlapping keys overwrite predecessor keys"""
    
    
    for ix, src in enumerate(srcs):
        if 'pkl' in src:
            with open(src, 'rb') as f:
                d = pickle.load(f)
        elif 'json' in src:
            with open(src, 'r') as f:
                d = json.load(f)
        else:
            raise ValueError("Only 'pkl' and 'json' files allowed")
        if ix == 0:
            d2 = d.copy()
        else:
            d2.update(d)
    return d2


def get_domain(web_address):
    """Return the domain of a URL or email address."""
    result = tldextract.extract(web_address)
    return '.'.join([result.domain, result.suffix])


def plot_pmf_cdf(x, bins=None, dst=None, xlim=None, xticks=None, weights=None):
    """Plot PMF and CDF as 2 x 1 sublplots."""


    sns.set(style="white", color_codes=True, font_scale=1.5)
    
    # Set up the matplotlib figure
    f, axes = plt.subplots(2, 1, figsize=(20, 7), sharex=True, sharey='row')
    if type(xlim) == tuple:
        [axes[x].set_xlim(xlim) for x in [0, 1]]
    sns.despine(left=True)
    if weights is None:
        weights = x
    
    # weighted and unweighted pmfs
    sns.distplot(x, kde=False, color='r', ax=axes[0], bins=bins, hist_kws={'weights': weights}, norm_hist=True)
    sns.distplot(x, kde=False, color='b', ax=axes[0], bins=bins, norm_hist=True)

    # weighted and unweighted cdfs
    sns.distplot(x, kde=False, bins=bins, color="r", ax=axes[1], hist_kws={'cumulative': True, 'weights': weights}, norm_hist=True)
    sns.distplot(x, kde=False, bins=bins, color="b", ax=axes[1], hist_kws={'cumulative': True}, norm_hist=True)

    if type(xticks) == list:
        plt.xticks(xticks)

    if type(dst) == str:
        plt.savefig(dst, bbox_inches='tight')
    plt.tight_layout()


def simplify_col_nms(li, r={'customer': ''
                          , 'bill': ''
                          , 'year': 'y'
                          , 'entity': 'ent'
                          , 'product': 'p'
                          , 'country': 'a2'
                          , 'category': 'cat'
                          , 'name': 'nm'
                          , 'email': 'em'
                          , '_each': ''
                          , 'quantity': 'q'
                          , 'date': 'dt'
                          , 'discount': 'disc'}):
    li2 = []
    for i in li:
        if i =='product_name':
            li2.append('p')
        elif i == 'customer_fullname':
            li2.append('c_fullnm')
        else:
            for k, v in r.items():
                i = i.replace(k, v)
            li2.append(i.strip('_'))
    return li2






def make_nonnegative(df):
    """Make negative values of numeric columns zero."""
    if type(df) != pd.core.frame.DataFrame:
        raise TypeError('Must supply function a Pandas dataframe')
    dtypes = (df.dtypes == np.float) | (df.dtypes == np.int)
    num_cols = dtypes[dtypes==True].index.values
    if len(num_cols) > 0:
        for num_col in num_cols:
            mask = df[num_col] < 0
            df.loc[mask, num_col] = 0
    else:
        print('No numeric columns to make non-negative')
    return df


def filter_with_dict(df, d):
    """Filter dataframe using dict made of column-value key-value pairs."""
    for col, values in d.items():
        df = df[df[col].isin(values)]
    return df


def iso2date(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()


def preview(df, nrows=1):
    """Preview top n and bottom n dataframe rows & print shape of dataframe."""
    print(df.shape)
    if type(df)==pd.core.series.Series:
        df = df.to_frame()

    if len(df) > 5:
        head = df.copy().head(nrows)
        head.loc['...'] = ['...'] * head.shape[1]
        tail = df.copy().tail(nrows)
        return pd.concat([head, tail])
    else:
        return df



def lower_strip(dataframe, verbose=False):
    columns = dataframe.columns.values
    for column in columns:
        if dataframe[column].dtypes == 'O':
            try:
                dataframe[column]= dataframe[column].apply(lambda x: str(x)).str.lower().str.strip()
            except:
                if verbose==True:
                    print('%s is not a string and could not be lowercased' % column)
    return dataframe


def pickle_outputs(df, _dir, filename, readme_message, excel=False, csv=False):
    """Pickle dataframe and generate readme."""

    with open(os.path.join(_dir, filename + '_readme.txt'), 'w') as f:
        f.write(readme_message)

    df.to_pickle(os.path.join(_dir, filename + '.pkl'))  # undated

    if excel == True:

        df.to_excel(os.path.join(_dir, filename + '.xlsx'))  # undated
    if csv == True:

        df.to_csv(os.path.join(_dir, filename + '.csv'))  # undated


def remove_punctuation(s):
    translator = str.maketrans('', '', string.punctuation)
    return s.translate(translator)


def replace_punctuation_with_underscore(s):
    a = '!"#$%&\'()*+, -./:;<=>?@[\\]^`{|}~'
    b = '________________________________'
    translator = str.maketrans(a, b)
    return s.translate(translator)



def drop_nulls(df, null_thresh=0.9, verbose=True):
    """Drop columns if fraction of nulls exceeds threshold."""
    if (null_thresh < 0) or (null_thresh > 1):
        raise ValueError('Threshold must be value from 0 to 1.')
    columns = df.columns.values.tolist()
    drop_cols = []
    for column in columns:
        null_count = pd.isnull(df[column]).sum()
        null_fraction = null_count / df.shape[0]
        if null_fraction > null_thresh:
            if verbose==True:
                print('Drop %s' % column)
            drop_cols.append(column)
    if len(drop_cols) > 0:
        return df.drop(axis=1, labels=drop_cols)
    return df


def concatenate_files(src_dir, encoding='utf-8'):
    """Concatenate csvs and xlsx files; must specify columns"""
    frames = []
    li = [glob.glob(os.path.join(src_dir, '*.' + x)) for x in ['csv', 'xlsx', 'pkl']]
    li = [item for sublist in li for item in sublist if len(sublist) > 0 ]
    for ix, src in enumerate(li):
        pct_complete = str(int(ix / float(len(li)) * 100))
        print('%s percent complete' % pct_complete)
        df = file_to_dataframe(src, encoding)
        frames.append(df)
    return pd.concat(frames, ignore_index=True).drop_duplicates()


def file_to_dataframe(src, encoding):
    """Load dataframe and clean column names.

    Input path of dataframe
    Replace col spaces w/ underscores & lowercase col names
    """
    if '.pkl' in src:
        dataframe = pd.read_excel(src)
    elif '.xlsx' in src:
        dataframe = pd.read_excel(src, encoding=encoding)

    elif '.csv' in src:
        dataframe = pd.read_csv(src, dtype, encoding=encoding, error_bad_lines=False, warn_bad_lines=True)
    else:
        raise ValueError('Fxn only loads files with csv, xlsx, and pickle extensions')
    dataframe.columns =\
        [x.replace(' ', '_').lower() for x in dataframe.columns]
    return dataframe


def filter_dates(dataframe, col, start_date, end_date='2050-12-31'):
    """Select dataframe rows that fall within specified date range.
    
    Output inclusive of start and end dates
    """
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    mask = (pd.to_datetime(dataframe[col]) >= start_date) & (pd.to_datetime(dataframe[col]) <= end_date)
    return dataframe[mask]


def assign_segments(dataframe, match_column, dictionary):
    """ Assigns segments based on key-value pairs in dictionary.

        Creates new column for each key.
    """

    for key, val in dictionary.items():
        if type(val) is list:
            val = '|'.join(val)
        dataframe[key] = dataframe[match_column].str.contains(val)
    return dataframe


def sum_over_periods(df, freq):
    # https://stackoverflow.com/questions/15799162/resampling-within-a-pandas-multiindex
    level_values = df.index.get_level_values
    return (df.groupby([level_values(i) for i in [0,1]]
                       +[pd.Grouper(freq=freq, level=-1)]).sum())


def make_break_labels(breaks):
    breaks[0], breaks[-1] = -1, max_quantity + 1  # finagle breaks list for use in pandas binning algorithm
    break_lows = [0] + [x + 1 for x in breaks[1:-1]]
    break_highs = breaks[1:]
    break_highs[-1] = max_quantity
    break_lows_highs = list(zip(break_lows, break_highs))
    return [str(x[0]) + '-' + str(x[1]) for x in break_lows_highs]


def divide_segment(dataframe, groupby_col, sum_col, name_col):
    groupby_df = dataframe.groupby(groupby_col)[sum_col].sum()
    groupby_df = pd.DataFrame(groupby_df).join(dataframe[[name_col, groupby_col]].set_index(groupby_col), how='left').drop_duplicates()

    groupby_df[name_col] = groupby_df[name_col].str.title()
    return groupby_df.groupby(name_col).sum().sort_values(by=sum_col, ascending=False)
    #return groupby_df.set_index(name_col)


def top_x(dataframe, number, groupby_col, sum_cols, other_label):
    """Consolidate categories that are not within the top x categories.
    If more than one sum col is given, sort done based on first sum col specified.
    sum_cols is a list
    """
    groupby = dataframe.groupby([groupby_col]).agg('sum').sort_values(by=sum_cols, ascending=[False] * len(sum_cols))[sum_cols]
    tops_ix = groupby.head(number-1).index.values
    mask = ~dataframe[groupby_col].isin(tops_ix)
    dataframe.loc[mask, groupby_col] = other_label
    return dataframe


def save_xls(list_dfs, xls_path, sheet_names=None):
    """Save list of dataframes to distinct worksheets of xlsx file."""
    writer = pd.ExcelWriter(xls_path)
    for ix, df in enumerate(list_dfs):
        if sheet_names is None:
            df.to_excel(writer, 'sheet%s' % ix)
        else:
            df.to_excel(writer, sheet_names[ix])
    writer.save()



def run_in_parallel(*fns):
    proc = []
    for fn in fns:
        p = multiprocessing.Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# SPELL CHECKER
# https://github.com/mattalcock/blog/blob/master/2012/12/5/python-spell-checker.rst



def words(text):
    return re.findall('[a-z]+', text.lower())


def train(features):
    model = collections.defaultdict(lambda: 1)
    for f in features:
        model[f] += 1
    return model


def load_big_text(src):
    with open(src) as file:
        big_text = file.read()

def get_NWORDS(big_text):
    NWORDS = train(words(big_text))
    return NWORDS

alphabet = 'abcdefghijklmnopqrstuvwxyz'


def edits1(word):
    s = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes    = [a + b[1:] for a, b in s if b]
    transposes = [a + b[1] + b[0] + b[2:] for a, b in s if len(b)>1]
    replaces   = [a + c + b[1:] for a, b in s for c in alphabet if b]
    inserts    = [a + c + b     for a, b in s for c in alphabet]
    return set(deletes + transposes + replaces + inserts)


def known_edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in NWORDS)


def known(words):
    return set(w for w in words if w in NWORDS)


def correct(word):
    candidates = known([word]) or known(edits1(word)) or    known_edits2(word) or [word]
    return max(candidates, key=NWORDS.get)
