import os, sys, time, re
import pymongo
import pandas as pd

DB_NAME = "cryptocurrency"
DB_USER = "supmit"
DB_PASS = "*******"
DB_PORT = 27017
DB_HOST = "localhost"

DEBUG = 1

COLLECTIONS = ['coinmarketcapdata', 'coinmarketdata', 'investdata', 'ohlcvdata', 'coinlayer']

STANDARD_METRICS = ['volume_total', 'volume_24hr', 'supply', 'percent_1hr', 'percent_24hr', 'percent_7d', 'curr_price', 'marketcap', ]

METRICS_COINMARKETCAPDATA = ['volume', 'percent7d', 'percent24hr', 'marketcap', 'supply', 'currency_price', 'percent1hr']
METRICS_COINMARKETDATA = ['percent_change_7days', 'percent_change_24hr', 'volume_24hr', 'percent_change_1hr', 'currency_price' ]
METRICS_INVESTDATA = ['volume_24hrs', 'market_cap', 'change_24hrs', 'change_7days', 'currency_price', 'total_volume' ]
METRICS_OHLCVDATA = ['trades_count', 'volume_traded', 'price_close', 'price_high', 'price_open', 'price_low' ]
#METRICS_COINBASE = [] # Not needed as it is directly shown from the website.
METRICS_COINLAYER = []

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

URL_PROTOCOL = "http://"
APP_URL_PREFIX = "http://cryptocurry.me:8002/"
LOGIN_URL = "cryptocurry/analyze/visual/dsentryiface/"
LOGIN_REDIRECT_URL = "cryptocurry/analyze/visual/dsentryiface/"
OPERATIONS_URL = "cryptocurry/analyze/visual/operations/"
REGISTER_URL = "cryptocurry/auth/register/"
LOGIN_URL = "cryptocurry/auth/login/"

PROFIMG_CHANGE_URL = "/cryptocurranalysis/changeimg/"
ACCTACTIVATION_URL = "cryptocurry/activate/"

"""
Patterns to be handled
"""
EMAIL_PATTERN = re.compile("[\w\.]*\@[\w\.]*", re.MULTILINE|re.DOTALL)
MULTIPLE_WS_PATTERN = re.compile(r"^\s*$", re.MULTILINE | re.DOTALL)
PHONENUM_PATTERN = re.compile(r"^\d+$", re.MULTILINE | re.DOTALL)
REALNAME_PATTERN = re.compile(r"^([a-zA-Z\s]*)$", re.MULTILINE | re.DOTALL)

"""
Passwords should have atleast this grade in a scale of 1 to 5.
Password strength is gauged by "check_passwd_strength()" function
(in static/pageutils.js) in frontend and by "check_password_strength()"
function (in cryptocurry/utils.py) in backend.
"""
MIN_ALLOWABLE_PASSWD_STRENGTH = 3

# Some application related variables:
PROFILE_PHOTO_NAME = "curryprofilepic"
PROFILE_PHOTO_EXT = ( "gif", "jpg", "jpeg", "png", "tiff", "tif" )
PROFILE_PHOTO_HEIGHT = 102 # in pixels
PROFILE_PHOTO_WIDTH = 102 # in pixels

# Max size of file that may be uploaded by user
MAX_FILE_SIZE_ALLOWED = 10000000

MAILSENDER = "admin@cryptocurry.me"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
# The above 2 config params should be turned on (True) once we start using https.
CSRF_COOKIE_NAME = "csrftoken"
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000 

COIN_MARKET_CAP_API_KEY = "*****************************"
COIN_MARKET_CAP_DOMAIN = "https://pro-api.coinmarketcap.com"

BLOCKCHAIN_API_KEY = "*****************************"

COINLAYER_ID = "cryptocurry.me@gmail.com"
COINLAYER_PASSWD = "************"
COINLAYER_COMPANY_NAME = "CryptoCurry Pvt. Ltd."
COINLAYER_API_KEY = "**********************************"
COINLAYER_LIVE_RATES_API_ENDPOINT = "http://api.coinlayer.com/api/live"
SELECTED_COINLAYER_CRYPTO_CODES = "BNB,BTC,EOS,LTC,XRP,ETH,BCH,ETC,XMR,XLM,BTG,NEO"
POLL_FREQUENCY = 2 # in hours. So there would be 12 calls per day, which means 360 calls a month.
# The current plan has a max limit of 500 calls per month.
# The codes are listed below with the names of the currencies:
# BNB : Binance Coin, BTC : Bitcoin, EOS : EOS, LTC : LiteCoin, XRP : Ripple, ETH : Ethereum, BCH : Bitcoin Cash, ETC : Ethereum Classic
# XMR : Monero, XLM : Stellar, BTG : Bitcoin Gold, NEO : NEO.
COINLAYER_NUM_DATETIMES = 3 # We want to see the last 3 date records only. Modify it to suit your needs.

SESSION_EXPIRY_LIMIT = 86400



