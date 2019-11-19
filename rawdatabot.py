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
    url = "https://www.investing.com/crypto/"
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
        print "Could not retrieve response from the request to https://www.investing.com/crypto/"
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


def coinmarketcap():
    url = "https://coinmarketcap.com/all/views/all/"
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler())
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : 'coinmarketcap.com', 'Referer' : 'https://www.google.com' }
    marketcap_request = urllib2.Request(url, None, http_headers)
    marketcap_response = None
    try:
        marketcap_response = opener.open(marketcap_request)
    except:
        print "Could not get the raw cryptocurrency data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    content = decodeGzippedContent(marketcap_response.read())
    soup = BeautifulSoup(content)
    if soup is None:
        print "Soup is empty."
        return False
    infolist = []
    mongoconn = pymongo.MongoClient("mongodb://%s:%s@localhost:%s/cryptocurrency"%(config.MONGO_USER, config.MONGO_PASSWD, config.MONGO_PORT))
    db = mongoconn.cryptocurrency
    currencytdlist = soup.findAll("a", {'class' : 'currency-name-container link-secondary'})
    for currencysoup in currencytdlist:
        currencyname = currencysoup.getText()
        symboltd = currencysoup.findNext("td", {'class' : 'text-left col-symbol'})
        symbol = symboltd.getText()
        marketcaptd = symboltd.findNext("td", {'class' : 'no-wrap market-cap text-right'})
        marketcap = marketcaptd.getText()
        marketcap = marketcap.replace("$", "")
        marketcap = marketcap.replace(",", "")
        if marketcap == "?":
            marketcap = 0.0
        priceanchor = marketcaptd.findNext("a", {'class' : 'price'})
        price = priceanchor.getText()
        price = price.replace("$", "")
        price = price.replace(",", "")
        if price == "?":
            price = 0.0
        supplyspan = priceanchor.findNext("span")
        supply = supplyspan.getText()
        supply = supply.replace("$", "")
        supply = supply.replace(",", "")
        if supply == "?":
            supply = 0.0
        volumeanchor = supplyspan.findNext("a", {'class' : 'volume'})
        volume = volumeanchor.getText()
        volume = volume.replace("$", "")
        volume = volume.replace(",", "")
        if volume == "?":
            volume = 0.0
        percent1hrtd = volumeanchor.findNext("td")
        percent1hr = percent1hrtd.getText()
        percent1hr = percent1hr.replace("$", "")
        percent1hr = percent1hr.replace(",", "")
        percent1hr = percent1hr.replace("%", "")
        if percent1hr == "?":
            percent1hr = 0.0
        percent24hrtd = percent1hrtd.findNext("td")
        percent24hr = percent24hrtd.getText()
        percent24hr = percent24hr.replace("$", "")
        percent24hr = percent24hr.replace(",", "")
        percent24hr = percent24hr.replace("%", "")
        if percent24hr == "?":
            percent24hr = 0.0
        percent7dtd = percent24hrtd.findNext("td")
        percent7d = percent7dtd.getText()
        percent7d = percent7d.replace("$", "")
        percent7d = percent7d.replace(",", "")
        percent7d = percent7d.replace("%", "")
        if percent7d == "?":
            percent7d = 0.0
        """
        if float(marketcap) > 0.0:
            print "MARKET CAP = %s\n"%marketcap
        """
        valdict = {'currency_name' : currencyname, 'currency_symbol' : symbol, 'marketcap' : marketcap, 'currency_price' : price, 'supply' : supply, 'volume' : volume, 'percent1hr' : percent1hr, 'percent24hr' : percent24hr, 'percent7d' : percent7d, 'entrydatetime' : str(datetime.datetime.now())}
        infolist.append(valdict)
        try:
            result = db.coinmarketcapdata.insert_one(valdict)
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
    scraperslist = [scrapeFromInvest, getDataFromCoinMarket, coinmarketcap, cci30index,] # Add scraper functions here.
    collectionEventLoop(scraperslist)






