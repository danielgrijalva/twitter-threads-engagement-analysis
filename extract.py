import re
import requests
from bs4 import BeautifulSoup
from transform import auth_twitter
from pprint import pprint

soup = BeautifulSoup(open('html.html', encoding='utf-8'), 'html.parser')



def get_tweet_ids():
    '''
        Get ID of the first tweet of every thread.
        Returns: list of tweet ids ['96019298391', '97018293201'...]
    '''

    threads = soup.find_all('a', class_='thread-card-wrap')
    return [re.findall('\d+', t['href'])[0] for t in threads]

def get_bot_replies():
    auth = auth_twitter()
    user = 'threadreaderapp'
    url = f'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name={user}&exclude_replies=false&include_rts=false&trim_user=true'

    replies = requests.get(auth=auth, url=url).json()

    ids = []
    for tweet in replies:
        try:
            ids.append(tweet['entities']['urls'][0]['expanded_url'])
        except IndexError:
            pass

    return ids


def get_thread_by_reply():
    replies = get_bot_replies()
    ids = [re.findall('\d+', requests.get(reply_url).url)[0] for reply_url in replies]

    return ids

# pprint(api.GetStatus('964531229512085507', '964559596235960321'))

# print(get_tweet_ids())