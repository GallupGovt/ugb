from src import inputs
from src import utilities
from src import make_blm_kw_list
from src import get_breitbart_comments
from src import process_breitbart_comments
from src import classify_guardian_articles
from src import get_guardian_comments
from src import process_buardian_comments
import os


if not os.path.isfile('config.py'):
    raise ValueError('Must create conifg.py in this directory and specify google_custom_search_cx and developerKey variables')


def main():

    print(80 * '@')
    print('Make BLM keywords for Breitbart article classification')
    make_blm_kw_list.main()


    print(80 * '@')
    print('Get Breitbart comments')
    get_breitbart_comments.main()


    print(80 * '@')
    print('Process Breitbart comments')
    process_breitbart_comments.main()


    print(80 * '@')
    print('Classify Guardian articles')
    classify_guardian_articles.main()


    print(80 * '@')
    print('Get Guardian comments')
    get_guardian_comments.main()


    print(80 * '@')
    print('Process Guardian comments')
    process_guardian_comments.main()


if __name__ == '__main__':
    main()
