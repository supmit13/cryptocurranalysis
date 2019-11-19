import os, sys, re, time
import simplejson as json
import pymongo
import conf.config as config
from StringIO import StringIO
import urllib, urllib2
import datetime

"""
This script is to be run once every day,
as scheduled in config.py file.
"""

if __name__ == "__main__":
    mongoconn = pymongo.MongoClient("mongodb://%s:%s@localhost:%s/cryptocurrency"%(config.MONGO_USER, config.MONGO_PASSWD, config.MONGO_PORT))
    db = mongoconn.cryptocurrency
    apikey = config.COINAPI_APIKEY
    limit = config.OHLCV_LIMIT
    currency_symbols = db.coinmarketcapdata.distinct("currency_symbol") # Since coinmarketcapdata is the most exhaustive list of currencies, we are considering it as our source.
    currency_dict = {}
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36', 'X-CoinAPI-Key' : config.COINAPI_APIKEY }
    for currsymbol in currency_symbols:
        cpreclist = db.coinmarketcapdata.find({'currency_symbol': currsymbol})
        if cpreclist.count() == 0:
            print "Couldn't find record for currency symbol %s. Nothing to do, continuing operations.\n"%currsymbol
            continue
        currencyname = cpreclist[0]['currency_name']
        url = "https://rest.coinapi.io/v1/ohlcv/%s/USD/latest?period_id=1HRS&limit=%s"%(currsymbol, str(config.OHLCV_LIMIT).strip())
        print url, "*****************\n"
        #print http_headers
        ohlcv_request = urllib2.Request(url, None, http_headers)
        ohlcv_response = None
        try:
            ohlcv_response = opener.open(ohlcv_request)
        except:
            print "Could not get the OHLCV data - Error: %s\n"%sys.exc_info()[1].__str__()
            continue
        ohlcv_list = json.loads(ohlcv_response.read())
        for ohlcv_dict in ohlcv_list:
            ohlcv_dict['currency_name'] = currencyname
            ohlcv_dict['currency_symbol'] = currsymbol
            ohlcv_dict['entrydatetime'] = str(datetime.datetime.now())
            try:
                result = db.ohlcvdata.insert_one(ohlcv_dict)
            except:
                print "Could not enter data in mongo db. Error: %s\n"%sys.exc_info()[1].__str__()
    print "Done dumping data"

        
