import time
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from unidecode import unidecode
import mysql.connector
import pandas as pd
from datetime import datetime, date
try:

    mydb = mysql.connector.connect(
      host="localhost",
      user="otaladesuyi",
      passwd="phanmium",
        database="twitterdb"
    )
    mycursor = mydb.cursor()
except Exception as e:
        with open('errors.txt', 'a') as f:
            f.write(str(e))
            f.write('\n')

'''
    This module fetches initial data from twitter for initial graphs. 
    Also Saves tweets from Twitter if tweets do not exist. 
    Challenge: If tweet do not exist, I Need to return control to the front end   
'''

'''
    Need to crate a generic errorlogger fxn that stores errors in an excel file 
'''

term ="NationalBoyfriendDay" #senti.return_term()
# print("term is: ", term)

# consumer key, consumer secret, access token, access secret.
ckey = "AeiEWXqrh9TEZpMK6D3JXgYeR"
csecret = "IA3ACrYMSOZqcOcWOguQBwOsy47VZCEvGLBYauVr0iWbO4Dehr"
atoken = "381209092-08RQEfpldp6hoZTqCZu2LztCZ6Ub6y1YII1OUkxa"
asecret = "WkZaxwbeZmmUWOZR7tM5wk2CePTuI4LF9laV04NvayXor"


class listener(StreamListener):
    '''
        Class to save tweets in db
    '''
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
    def on_data(self, data):
        try:
            data = json.loads(data)
            tweet = unidecode(data['text'])
            time_ms = int(data['timestamp_ms'])/1000
            time_ms= datetime.utcfromtimestamp(time_ms).strftime('%Y-%m-%d %H:%M:%S')
            vs = self.analyzer.polarity_scores(tweet)
            sentiment = vs['compound']
            mycursor.execute("INSERT INTO sentiment (date, tweet, sentiment, term) VALUES (%s, %s, %s,%s)",
                      (time_ms, tweet, sentiment, term))
            print("Just inserted the following record: time: {}, tweet: {}, sentiment: {}, term: {}".format(time_ms,
                                                                                                                tweet,
                                                                                                                sentiment,
                                                                                                                term))
            mydb.commit()

        except KeyError as e:
            print('we got real bitch problems: at listener.on_data',str(e))
        return True

    def on_error(self, status):
        print('we got real bitch problems: from listener.on_error', status)


def check_term(term):
    try:
        df = pd.read_sql("SELECT * FROM sentiment WHERE term LIKE %s ORDER BY date DESC LIMIT 500", mydb,
                         params=('%' + term + '%',))
        if df.notnull:
            mydb.close()
            return df
            # return update_graph_scatter(df)
        else:
            scrape(term)
            # return null df
            # return game graph
    except Exception as e:
        with open('errors.txt', 'a') as f:
            towrite='error from check_term on the ' + str(date.today()) + str(e)
            f.write(towrite)
            f.write('\n')


def format_df(df):
    # df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df) / 2)).mean()
    # df['unix'] /= 1000
    # df['date'] = pd.to_datetime(df['date'])
    df.sort_values('date', inplace=True)
    df.set_index('date', inplace=True)
    df = df.resample('5min').mean()
    df.dropna(subset=['sentiment'], inplace=True)
    return df


def fetch_initial_tweets():
    try:
        df = pd.read_sql("SELECT * FROM sentiment ORDER BY date DESC LIMIT 500", mydb)
        mydb.close()
        # df = format_df(df)
        return df
    except Exception as e:
        with open('dberrors.txt', 'a') as f:
            towrite='error from fetch_initial_tweets on the ' + str(date.today()) + str(e)
            f.write(towrite)
            f.write('\n')
        print('we got real bitch problems: at twitterLive.py.fetch_initial_tweets', str(e))
        return True


def scrape(senti_term):
    while True:
        try:
            auth = OAuthHandler(ckey, csecret)
            auth.set_access_token(atoken, asecret)
            twitterStream = Stream(auth, listener())
            twitterStream.filter(track=[str(senti_term)])
        except Exception as e:
            with open('scrapping_errors.txt', 'a') as f:
                towrite = 'error from function scrape in TwitterLive.py on the ' + str(date.today()) + str(e)
                f.write(towrite)
                f.write('\n')
            print(str(e))
            time.sleep(5)



#check_term(term)