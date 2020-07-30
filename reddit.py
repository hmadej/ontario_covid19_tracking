import praw
import asciichartpy
from decouple import config

client_id = config('client_id')
client_secret = config('client_secret')
username = config('username')
password = config('password')



def send_update(data, plots, url):
    case_count = data['case count']
    test_count = data['test count']
    date = data['date']
    rt = data["r_t"]
    case100k = data["case per 100k"]
    positivity = data["positivity"]
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         user_agent='py',
                         username=username,
                         password=password)

    reply_str_1 = f'Key indicators for {date} \n\n Infection rate: __{rt}__ \n\n __{case100k:2.2f}__ cases per 100k \n\n'
    reply_str_2 = f'__{positivity:2.2f}%__ positivity rate \n\n Infection rate for last 70 days: \n\n{asciichartpy.plot(plots["rt"][-70:], {"height": 10})}'
    reply_str_3 = '\n\nThe method for modeling reproductive number can be found [here](' \
                  'https://github.com/rtcovidlive/covid-model), based on [accurate episode date](' \
                  'https://data.ontario.ca/dataset/confirmed-positive-cases-of-covid-19-in-ontario) '
    subreddit = reddit.subreddit('secret_secret_secret')
    post = subreddit.submit(f'{date} COVID-19 Update: {case_count} new cases, {test_count} tests completed', url=url)
    post.reply(reply_str_1 + reply_str_2 + reply_str_3)
