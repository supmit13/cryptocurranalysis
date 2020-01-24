import os, sys, re, time
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import gzip
from StringIO import StringIO
import MySQLdb
import simplejson as json
import datetime
import pandas as pd
import pymongo
import conf.config as config
from cryptocurry.crypto_settings import *
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

sleeptime = config.SLEEPTIME

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


def scrapeFromInvest():
    url = "https://www.investing.com/crypto/currencies"
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler())
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : 'www.investing.com', 'Referer' : 'https://www.google.com' }
    investing_request = urllib2.Request(url, None, http_headers)
    investing_response = None
    try:
        investing_response = opener.open(investing_request)
    except:
        print "Could not get the raw cryptocurrency data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    if not investing_response:
        print "Could not retrieve response from the request to https://www.investing.com/crypto/currencies"
        return False
    investing_data_enc = investing_response.read()
    investing_data = decodeGzippedContent(investing_data_enc)
    #print investing_data
    soup = BeautifulSoup(investing_data)
    datatds = soup.findAll("td", {'class' : 'flag'})
    mongoconn = pymongo.MongoClient("mongodb://%s:%s@localhost:%s/cryptocurrency"%(config.MONGO_USER, config.MONGO_PASSWD, config.MONGO_PORT))
    db = mongoconn.cryptocurrency
    for td in datatds:
        currnametd = td.findNext('td')
        currname = currnametd['title']
        currnametd = currnametd.findNext('td')
        currsymbol = currnametd['title']
        currnametd = currnametd.findNext('td')
        currprice = currnametd.getText()
        currprice = currprice.replace("$", "")
        currprice = currprice.replace(",", "")
        currnametd = currnametd.findNext('td')
        market_cap = currnametd.getText()
        market_cap = market_cap.replace("&#x24;", "")
        currnametd = currnametd.findNext('td')
        vol24h = currnametd.getText()
        vol24h = vol24h.replace("&#x24;", "")
        currnametd = currnametd.findNext('td')
        totalvol = currnametd.getText()
        totalvol = totalvol.replace('%', '')
        currnametd = currnametd.findNext('td')
        chg24h = currnametd.getText()
        chg24h = chg24h.replace('+', "")
        chg24h = chg24h.replace('%', "")
        currnametd = currnametd.findNext('td')
        chg7d = currnametd.getText()
        chg7d = chg7d.replace('+', "")
        chg7d = chg7d.replace('%', "")
        mongodata = {'currency_name' : currname, 'currency_symbol' : currsymbol, 'currency_price' : currprice, 'market_cap' : market_cap, 'volume_24hr' : vol24h, 'total_volume' : totalvol, 'change_24hr' : chg24h, 'change_7days' : chg7d, 'entrydatetime' : str(datetime.datetime.now())}        
        try:
            result = db.investdata.insert_one(mongodata)
        except:
            print "Could not enter data in mongo db. Error: %s\n"%sys.exc_info()[1].__str__()
    print "Done collecting data from investing at %s...\n"%str(datetime.datetime.now())
    return True


def getDataFromCoinMarket():
    coinmarketapikey = "edc74898-5367-43bf-b3cb-2af1ab8b42b7"
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler())
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : 'pro-api.coinmarketcap.com', 'X-CMC_PRO_API_KEY' : coinmarketapikey } 
    listings_latest_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?sort=market_cap&start=1&limit=50&convert=USD&cryptocurrency_type=coins"
    listings_request = urllib2.Request(listings_latest_url, None, http_headers)
    listings_response = None
    try:
        listings_response = opener.open(listings_request)
    except:
        print "Could not get the cryptocurrency listings data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    if not listings_response:
        print "Could not retrieve response from the request to https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        return False
    listings_data_enc = listings_response.read()
    listings_data = decodeGzippedContent(listings_data_enc)
    #print listings_data
    listings_dict = json.loads(listings_data)
    listings_data_list = listings_dict['data']
    curr_data_map = {}
    mongoconn = pymongo.MongoClient("mongodb://%s:%s@localhost:%s/cryptocurrency"%(config.MONGO_USER, config.MONGO_PASSWD, config.MONGO_PORT))
    db = mongoconn.cryptocurrency
    for elemdict in listings_data_list:
        idno = elemdict['id']
        name = elemdict['name']
        volume_24h = elemdict['quote']['USD']['volume_24h']
        price = elemdict['quote']['USD']['price']
        percent_change_1h = elemdict['quote']['USD']['percent_change_1h']
        percent_change_24h = elemdict['quote']['USD']['percent_change_24h']
        percent_change_7d = elemdict['quote']['USD']['percent_change_7d']
        last_updated = elemdict['quote']['USD']['last_updated']
        mongodata = {'idno' : str(idno), 'currency_name' : name, 'currency_price' : price, 'volume_24hr' : volume_24h, 'percent_change_1hr' : percent_change_1h, 'percent_change_24hr' : percent_change_24h, 'percent_change_7days' : percent_change_7d, 'last_updated' : last_updated, 'entrydatetime' : str(datetime.datetime.now())}
        try:
            result = db.coinmarketdata.insert_one(mongodata)
        except:
            print "Could not enter data in mongo db. Error: %s\n"%sys.exc_info()[1].__str__()
    print "Collected data from coinmarket at %s...\n"%str(datetime.datetime.now())
    return curr_data_map


"""
This uses the coinmarketcap API - Basic Plan (Free).
"""
def coinmarketcap():
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
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
        print "Could not collect data from CoinMarketCap. Returning."
        return 0
    infolist = []
    mongoconn = pymongo.MongoClient("mongodb://%s:%s@localhost:%s/cryptocurrency"%(config.MONGO_USER, config.MONGO_PASSWD, config.MONGO_PORT))
    db = mongoconn.cryptocurrency
    cryptocurrencydatalist = data[u'data']
    infolist = []
    #mongoconn = pymongo.MongoClient("mongodb://%s:%s@localhost:%s/cryptocurrency"%(config.MONGO_USER, config.MONGO_PASSWD, config.MONGO_PORT))
    for cryptodict in cryptocurrencydatalist:
        last_updated, entrydatetime, cryptocurrname, cryptosymbol, marketcap,price, supply, volume, percent_change_1h, percent_change_24h, percent_change_7d = "", "", "", "", "", "", "", "", "", "", "" 
        entrydatetime = str(datetime.datetime.now())
        if cryptodict.has_key('last_updated'):
            last_updated = cryptodict['last_updated']
        else:
            last_updated = entrydatetime
        if cryptodict.has_key(u'name'):
            cryptocurrname = cryptodict[u'name']
        else:
            continue # If no name is found, then it is not of much use to us.
        if cryptodict.has_key(u'symbol'):
            cryptosymbol = cryptodict[u'symbol']
        else:
            cryptosymbol = cryptocurrname
        if cryptodict.has_key(u'quote') and cryptodict[u'quote'].has_key('USD') and cryptodict[u'quote'][u'USD'].has_key(u'market_cap'):
            marketcap = cryptodict[u'quote'][u'USD'][u'market_cap']
        else:
            marketcap = 0.00
        if cryptodict.has_key(u'quote') and cryptodict[u'quote'].has_key('USD') and cryptodict[u'quote'][u'USD'].has_key(u'price'):
            price = cryptodict[u'quote'][u'USD'][u'price']
        else:
            price = 0.00
        if cryptodict.has_key(u'total_supply'):
            supply = cryptodict['total_supply']
        else:
            supply = 0
        if cryptodict.has_key(u'quote') and cryptodict[u'quote'].has_key('USD') and cryptodict[u'quote'][u'USD'].has_key(u'volume_24h'):
            volume = cryptodict[u'quote'][u'USD'][u'volume_24h']
        else:
            volume = 0.00
        if cryptodict.has_key(u'quote') and cryptodict[u'quote'].has_key('USD') and cryptodict[u'quote'][u'USD'].has_key(u'percent_change_1h'):
            percent_change_1h = cryptodict[u'quote'][u'USD'][u'percent_change_1h']
        else:
            percent_change_1h = 0.00
        if cryptodict.has_key(u'quote') and cryptodict[u'quote'].has_key('USD') and cryptodict[u'quote'][u'USD'].has_key(u'percent_change_24h'):
            percent_change_24h = cryptodict[u'quote'][u'USD'][u'percent_change_24h']
        else:
            percent_change_24h = 0.00
        if cryptodict.has_key(u'quote') and cryptodict[u'quote'].has_key('USD') and cryptodict[u'quote'][u'USD'].has_key(u'percent_change_7d'):
            percent_change_7d = cryptodict[u'quote'][u'USD'][u'percent_change_7d']
        else:
            percent_change_7d = 0.00
        valdict = {'currency_name' : cryptocurrname, 'currency_symbol' : cryptosymbol, 'marketcap' : marketcap, 'currency_price' : price, 'supply' : supply, 'volume' : volume, 'percent1hr' : percent_change_1h, 'percent24hr' : percent_change_24h, 'percent7d' : percent_change_7d, 'entrydatetime' : str(last_updated)}
        infolist.append(valdict)
        try:
            result = db.coinmarketcapdata.insert_one(valdict)
            #print valdict,"\n\n"
        except:
            print "Could not enter data in mongo db. Error: %s\n"%sys.exc_info()[1].__str__()
    print "Collected data from coinmarketcap website.\n"
    return infolist


        
"""
This is an index for 30 cryptocurrencies combined on some mathematical basis. This
information is useful to those who want to invest in cryptocurrencies and hedge
their risks by putting various sums in the 30 selected cryptocurrencies. In order to
know more, please to the explanation at https://cci30.com/

"""
def cci30index():
    cci30url = "https://cci30.com/ajax/getIndexHistory.php"
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler())
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : 'coinmarketcap.com', 'Referer' : 'https://www.google.com' }
    cci30_request = urllib2.Request(cci30url, None, http_headers)
    cci30_response = None
    try:
        cci30_response = opener.open(cci30_request)
    except:
        print "Could not get the raw cryptocurrency data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    content = decodeGzippedContent(cci30_response.read())
    # content is a csv formatted data set
    mongoconn = pymongo.MongoClient("mongodb://%s:%s@localhost:%s/cryptocurrency"%(config.MONGO_USER, config.MONGO_PASSWD, config.MONGO_PORT))
    db = mongoconn.cryptocurrency
    headers = []
    records = []
    alldata = []
    datarecs = content.split("\n")
    headers = datarecs[0].split(",")
    for i in range(headers.__len__()):
        headers[i] = headers[i].strip() # Remove whitespace characters
    for datastr in datarecs:
        datalist = datastr.split(",")
        for i in range(1, datalist.__len__()):
            datalist[i] = datalist[i].strip()
        records.append(datalist)
    for recdata in records[1:]:
        ictr = 0
        datadict = {}
        for rdata in recdata:
            datadict[headers[ictr]] = rdata
            ictr += 1
            if ictr == headers.__len__():
                break
        try:
            result = db.cci30data.insert_one(datadict)
            alldata.append(datadict)
        except:
            print "Error: ", sys.exc_info()[1].__str__(), "\n"
    print "collected data from cci30 index at %s"%datetime.datetime.now()
    return alldata


"""
There doesn't seem to be any fucking location that provides a feed, either as an
API or as some screen data. How do I get the data from this asshole? Don't say I 
have to pay to get it, 'cause if that is so, then they are going to get troubled
by illegal means.... Accidents happen all the time, buildings collapse for
no apparent reason, fire breaks out for myriad reasons, bank accounts get hacked,
footage of senior executives in a compromizing situations come out of nowhere,
people show up at the wrong place at the wrong time, and then they vanish... 
Hmmmmm.... your actions route your life.
"""
def bloombergcryptoindex():
    url = "https://www.bloomberg.com/professional/product/indices/bloomberg-galaxy-crypto-index/"

"""
Get realtime currency data from coinlayer. 
"""
def getcoinlayerinfo():
    api_key = COINLAYER_API_KEY
    api_endpoint = COINLAYER_LIVE_RATES_API_ENDPOINT
    target_url = api_endpoint
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler())
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : 'coinlayer.com', 'Referer' : 'https://api.coinlayer.com' }
    symbols = "BNB,BTC,EOS,LTC,XRP,ETH,BCH,ETC,XMR,XLM,BTG,NEO"
    target_url += "?access_key=" + api_key + "&symbols=" + symbols
    coin_layer_request = urllib2.Request(target_url, None, http_headers)
    coin_layer_response = None
    try:
        coin_layer_response = opener.open(coin_layer_request)
    except:
        print "Could not get the raw cryptocurrency data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    jsoncontent = decodeGzippedContent(coin_layer_response.read())
    content = json.loads(jsoncontent)
    codesdict = {'BNB' : 'Binance Coin', 'BTC' : 'Bitcoin', 'EOS' : 'EOS', 'LTC' : 'Litecoin', 'XRP' : 'Ripple', 'ETH' : 'Ethereum', 'BCH' : 'Bitcoin Cash', 'ETC' : 'Ethereum Classic', 'XMR' : 'Monero', 'XLM' : 'Stellar', 'BTG' : 'Bitcoin Gold', 'NEO' : 'NEO'}
    mongoconn = pymongo.MongoClient("mongodb://%s:%s@localhost:%s/cryptocurrency"%(config.MONGO_USER, config.MONGO_PASSWD, config.MONGO_PORT))
    db = mongoconn.cryptocurrency
    currdatetime = datetime.datetime.now()
    content = db.coinlayer.insert_one({'currdatetime' : currdatetime, 'BNB' : content['rates']['BNB'], 'BTC' : content['rates']['BTC'], 'EOS' : content['rates']['EOS'], 'LTC' : content['rates']['LTC'], 'XRP' : content['rates']['XRP'], 'ETH' : content['rates']['ETH'], 'BCH' : content['rates']['BCH'], 'ETC' : content['rates']['ETC'], 'XMR' : content['rates']['XMR'], 'XLM' : content['rates']['XLM'], 'BTG' : content['rates']['BTG'], 'NEO' : content['rates']['NEO']})
    print "\n\nData added to coinlayer DB\n"
    return content


def collectionEventLoop(scraper_functions_list):
    lasttime = 0
    while True:
        currtime = time.time()
        if currtime - lasttime < sleeptime: # if we scraped within the last 'sleeptime', we go to sleep
            time.sleep(sleeptime)
            continue
        for i in range(0, scraper_functions_list.__len__()):
            scraper_functions_list[i]()
        lasttime = currtime


if __name__ == "__main__":
    scraperslist = [scrapeFromInvest, getDataFromCoinMarket, coinmarketcap, cci30index, getcoinlayerinfo,] # Add scraper functions here.
    collectionEventLoop(scraperslist)






