from transform import get_thread_ids, get_tweet_data, thread_to_pandas
from pprint import pprint

from tweets import *

threads = get_thread_ids(ten_fifteen)

d = get_tweet_data(threads)

thread_to_pandas(d, 'ten_fifteen.csv')