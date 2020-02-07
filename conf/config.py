import os, sys, re
"""
This file provides configuration for the CoinLayer to function appropriately.
"""
SLEEPTIME = 7200 # This is necessary for coinlayer to function properly.

MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_USER = "supmit"
MONGO_PASSWD = "spmprx"

GMAIL_USERNAME = "cryptocurry.me@gmail.com"
GMAIL_PASSWORD= "***********"

COINAPI_APIKEY = "*****************************"
OHLCV_INTERVAL = 24 # should be run once every day
OHLCV_LIMIT = 24 # Get 1 record for every hour
COINAPI_URL = "https://rest.coinapi.io"

