import os, sys, re, time
import urllib, urllib2
import gzip
from StringIO import StringIO
import json
import datetime
import pymongo
import conf.config as config
from cryptocurry.crypto_settings import *




class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302 


def decodeGzippedContent(encoded_content):
    response_stream = StringIO(encoded_content)
    decoded_content = ""
    try:
        gzipper = gzip.GzipFile(fileobj=response_stream)
        decoded_content = gzipper.read()
    except: # Maybe this isn't gzipped content after all....
        decoded_content = encoded_content
    return(decoded_content)


def getmongoclient():
    client = pymongo.MongoClient(port=config.MONGO_PORT)


def coinmarketcap():
    #print "HERE>>>\n"
    url = COIN_MARKET_CAP_DOMAIN + "/v1/cryptocurrency/listings/latest"
    #print url
    data = {'start' : 1, 'limit' : 1000, 'convert' : 'USD', 'sort' : 'name', 'sort_dir' : 'asc' , 'aux' : 'market_cap_by_total_supply,volume_24h_reported,volume_7d,total_supply,cmc_rank,date_added'}
    dataenc = urllib.urlencode(data)
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler())
    http_headers = { 'Accept' : 'application/json', 'Host' : 'coinmarketcap.com', 'X-CMC_PRO_API_KEY' : COIN_MARKET_CAP_API_KEY }
    marketcap_request = urllib2.Request(url, dataenc, http_headers)
    marketcap_response = None
    try:
        marketcap_response = opener.open(marketcap_request)
    except:
        print "Could not get the raw cryptocurrency data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    content = decodeGzippedContent(marketcap_response.read())
    print content
    

if __name__ == "__main__":
    coinmarketcap()


