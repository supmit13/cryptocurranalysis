#This example uses Python 2.7 and the python-request library.

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os, sys, re, time
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import gzip
from StringIO import StringIO
import datetime
import pymongo
import conf.config as config
from cryptocurry.crypto_settings import *


def cmcdata():
    url = COIN_MARKET_CAP_DOMAIN + '/v1/cryptocurrency/listings/latest'
    parameters = {
      'start':'1',
      'limit':'100',
      'convert':'USD'
    }
    headers = {
      'Accepts': 'application/json',
      'X-CMC_PRO_API_KEY': COIN_MARKET_CAP_API_KEY,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        print(data)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

if __name__ == "__main__":
    cmcdata()

  
