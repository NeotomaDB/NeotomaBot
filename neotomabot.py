#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!python3
""" Neotoma Database Twitter Manager v2.0
    by: Simon Goring
    This Twitter bot is intended to provide updated information to individuals about additions to the Neotoma
    Paleoecology database.  The script leverages the `schedule` package for Python, running continually in 
    the background, sending out tweets at a specified time and interval.
""" 

from TwitterAPI import TwitterAPI
import random
import xmltodict
import urllib.request
import schedule
import time
import os

twitstuff = {'consumer_key':os.environ['consumer_key'], 
             'consumer_secret': os.environ['consumer_secret'],
             'access_token_key':os.environ['access_token_key'],
             'access_token_secret':os.environ['access_token_secret']}

datasets = set()

api = TwitterAPI(consumer_key=twitstuff['consumer_key'], 
                 consumer_secret=twitstuff['consumer_secret'], 
                 access_token_key=twitstuff['access_token_key'], 
                 access_token_secret=twitstuff['access_token_secret'])

def twitterup(api):
  line = "Someone just restarted me by pushing to GitHub.  This means I've been updated, yay!"
  api.request('statuses/update', {'status':line})

def randomtweet(api):
    """ Tweet a random statement from a plain text document. Passing in the twitter API object.
        The tweets are all present in the file `resources/cannedtweets.txt`.  These can be edited
        directly on GitHub if anyone chooses to.
    """
    with open('resources/cannedtweets.txt', 'r') as f:
        alltweets = f.read().splitlines()
        line = random.choice(alltweets)
        api.request('statuses/update', {'status':line})
        
def recentsite(api):
    """ Tweet one of the recent data uploads from Neotoma. Passing in the twitter API object.
        This leverages the v1.5 API's XML response for recent uploads.  It selects one of the new uploads
        (except geochronology uploads) and tweets it out.  It selects them randomly, and adds the selected 
        dataset to a set object so that values cannot be repeatedly tweeted out.
    """
    with urllib.request.urlopen('https://api.neotomadb.org/v1.5/data/recentuploads/1') as response:
        html = response.read()
        output = xmltodict.parse(html)['results']['results']
        records = list(filter(lambda x: x['record']['datasettype'] != 'geochronology' or x['record']['datasetid'] not in datasets, output))
    if len(records) > 0:
        tweet = random.choice(records)['record']
        while tweet['datasetid'] in datasets:
            tweet = random.choice(records)['record']
        string = "It's a new {datasettype} dataset from the {databasename} at {sitename}! https://data.neotomadb.org/{datasetid}".format(**tweet)
        if len(string) < 280:
            api.request('statuses/update', {'status':string})
            datasets.add(tweet['datasetid'])
        else:
            string = "It's a new dataset from the {databasename} at {sitename}! https://data.neotomadb.org/{datasetid}".format(**tweet)
            if len(string) < 280:
                api.request('statuses/update', {'status':string})
                datasets.add(tweet['datasetid'])


def self_identify_hub(api):
  """ Identify the codebase for the bot through a tweet. """
  line = 'This twitter bot for the Neotoma Paleoecological Database is programmed in #python and publicly available through an MIT License on GitHub: https://github.com/NeotomaDB/neotomabot'
  api.request('statuses/update', {'status':line})

twitterup(api)

schedule.every(6).hours.do(recentsite, api)
schedule.every(5).hours.do(randomtweet, api)
schedule.every().monday.at("14:30").do(self_identify_hub, api)
schedule.every().day.at("10:30").do(other_inf_hub, api)

while 1:
    schedule.run_pending()
    time.sleep(61)
