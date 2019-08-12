import os, sys, time, re
import pymongo
import pandas as pd

DB_NAME = "cryptocurrency"
DB_USER = "supmit"
DB_PASS = "spmprx"
DB_PORT = 27017
DB_HOST = "localhost"

COLLECTIONS = ['coinmarketcapdata', 'coinmarketdata', 'investdata', 'ohlcvdata']

METRICS = ['volume_total', 'volume_24hr', 'supply', 'percent_1hr', 'percent_24hr', 'percent_7d', 'curr_price', 'marketcap', ]


