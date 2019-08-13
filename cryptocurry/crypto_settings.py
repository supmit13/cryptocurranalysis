import os, sys, time, re
import pymongo
import pandas as pd

DB_NAME = "cryptocurrency"
DB_USER = "supmit"
DB_PASS = "spmprx"
DB_PORT = 27017
DB_HOST = "localhost"

COLLECTIONS = ['coinmarketcapdata', 'coinmarketdata', 'investdata', 'ohlcvdata', 'coinbase']

METRICS = ['volume_total', 'volume_24hr', 'supply', 'percent_1hr', 'percent_24hr', 'percent_7d', 'curr_price', 'marketcap', ]

METRICS_COINMARKETCAPDATA = ['volume', 'percent7d', 'percent24hr', 'marketcap', 'supply', 'currency_price', 'percent1hr']
METRICS_COINMARKETDATA = ['percent_change_7days', 'last_updated', 'percent_change_24hr', 'volume_24hr', 'percent_change_1hr', 'currency_price' ]
METRICS_INVESTDATA = ['volume_24hr', 'market_cap', 'change_24hr', 'change_7days', 'currency_price', 'total_volume' ]
METRICS_OHLCVDATA = ['trades_count', 'volume_traded', 'price_close', 'price_high', 'price_open', 'price_low' ]
METRICS_COINBASE = [] # Not needed as it is directly shown from the website.

HEXCODE_CHAR_MAP = { \
        '%20' : " ", \
        '%27' : "'", \
        '%22' : '"', \
        '%24' : '$', \
        '%25' : '%', \
        '%26' : '&', \
        '%2A' : '*', \
        '%2B' : '+', \
        '%2E' : '.', \
        '%2F' : '/', \
    }

HTML_ENTITIES_CHAR_MAP = { \
        '&lt;' : '<', \
        '&gt;' : '>', \
        '&amp;': '&', \
        '&nbsp;' : ' ', \
        '&quot;' : '"', \
        '&#91;' : '[', \
        '&#93;' : ']', \
        '&#39;' : '"',\
    }

INV_HEXCODE_CHAR_MAP = { \
        " " : '%20', \
        "'" : '%27', \
    '"' : '%22', \
    '$' : '%24', \
    '&' : '%26', \
    '*' : '%2A', \
    '+' : '%2B', \
    '.' : '%2E', \
    '/' : '%2F', \
    }

INV_HTML_ENTITIES_CHAR_MAP = { \
    '<' : '&lt;', \
    '>' : '&gt;', \
    '&' : '&amp;', \
    ' ' : '&nbsp;', \
    '"' : '&quot;', \
    '[' : '&#91;', \
    ']' : '&#93;', \
    '"' : '&#39;', \
    }


