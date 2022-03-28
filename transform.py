import os
import requests
from requests_oauthlib import OAuth1
import pandas as pd
from bs4 import BeautifulSoup
import time
import datetime
from pprint import pprint
from operator import itemgetter

def auth_twitter():
    CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
    CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
    ACCESS_KEY = os.environ.get('ACCESS_KEY')
    ACCESS_SECRET = os.environ.get('ACCESS_SECRET')

    auth_url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)

    requests.get(auth_url, auth=auth)

    return auth

def get_thread_ids(original_tweet_ids):
    ids = []
    for original in original_tweet_ids:
        headers= {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
            'Referer': 'https://twitter.com/statuses/' + original,
            'Upgrade-Insecure-Requests': '1',
            'Host': 'twitter.com',
            'DNT': '1',
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'en-US',
        }
        page = requests.get('https://twitter.com/statuses/' + original, headers=headers).content
        soup = BeautifulSoup(page, 'html.parser')

        replies_number = get_thread_replies(soup)
        thread = soup.find('li', class_='ThreadedConversation ThreadedConversation--selfThread')

        if thread:
            # check if thread too long
            if not thread.find('div', class_='ThreadedConversation-tweet last'):
                # if too long (30+ tweets in the thread) move onto the next thread
                print('Thread too long.', original)
                continue
            else:
                tweets_in_thread = thread.find_all('div', class_='ThreadedConversation-tweet')

                full_thread = [tweet.find('li')['data-item-id'] for tweet in tweets_in_thread]
                full_thread.insert(0, original)

                ids.append({'thread': full_thread, 'replies_number': replies_number})
        else:
            # 404
            # some people delete the threads 'cause too many replies/notifications
            print('Thread doesn\'t exist anymore.', original)
            continue

    return ids

def get_thread_replies(soup):
    '''Number of replies along the thread.'''
    original = soup.find('div', class_='permalink-inner permalink-tweet-container')
    
    # first # of replies
    try:
        first_replies_number = [int(
                original.find(
                        'span', 
                        class_='ProfileTweet-action--reply'
                    ).find(
                        'span', 
                        class_='ProfileTweet-actionCount'
                        )['data-tweet-stat-count']
            )]

        print(first_replies_number)
        rest_of_replies = soup.find(
                            'li', class_='ThreadedConversation ThreadedConversation--selfThread'
                            ).find_all('button', class_='js-actionReply')
        
        rest_of_replies_number = [int(r.find('span', class_='ProfileTweet-actionCountForPresentation').text or 0) for r in rest_of_replies]    

        return first_replies_number + rest_of_replies_number

    except AttributeError as ex:
        print(ex)
        pass


def get_tweet_data(threads):
    auth = auth_twitter()
    data = []

    for thread in threads:
        thread_raw_data = requests.get(auth=auth, 
                        url='https://api.twitter.com/1.1/statuses/lookup.json?trim_user=1&include_entities=0&id='
                        + ','.join(thread['thread'])).json()

        thread_data = date_to_timestamp(thread_raw_data)
        # twitter returns the tweets unordered,
        # so, let's sort by `created_at` so the threads are ordered
        # note: some automated thread tools tweet at the same exact moment
        # e.g. `Sat 16 Feb 12:30:01` for 1-3 tweets in the thread
        # so, some threads might remain unordered.
        sorted_thread_data = sorted(thread_data, key=itemgetter('timestamp'))

        for i, t in enumerate(sorted_thread_data):
            t['replies_number'] = thread['replies_number'][i]

        data.append(sorted_thread_data)                      

    return data

def date_to_timestamp(thread):
    for tweet in thread:
        date_str = tweet['created_at']
        tweet['timestamp'] = int(datetime.datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y').timestamp())

    return thread

def thread_to_pandas(threads, filename):
    thread_formatted = []    
    for i, thread in enumerate(threads):
        for tweet in thread:
            thread_number = i + 1
            tweet = {
                        'thread_id': f'Thread {thread_number}',
                        'id': tweet['id'],
                        'created_at': tweet['created_at'],
                        'timestamp': tweet['timestamp'],
                        'text': tweet['text'],
                        'favorite_count': tweet['favorite_count'],
                        'retweet_count': tweet['retweet_count'],
                        'reply_count': tweet['replies_number'],                        
                    }
            
            thread_formatted.append(tweet)

        df = pd.DataFrame(thread_formatted)
        df.to_csv(filename)
