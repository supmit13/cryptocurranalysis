import os, sys, re, time
import gzip
import simplejson as json
import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as mlt
import matplotlib.dates as mdates
#import scikit-learn as sk
import pymongo
import datetime
import cPickle, urlparse
import decimal, math, base64
from passlib.hash import pbkdf2_sha256 # To create hash of passwords
from pandas.plotting import register_matplotlib_converters

import cryptocurry.errors as err
import cryptocurry.utils as utils
from cryptocurry.crypto_settings import * 

from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie, requires_csrf_token
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.db.models import Q
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.template import Template, Context
from django.template.loader import get_template
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.backends.db import SessionStore
from django.middleware.csrf import get_token


@ensure_csrf_cookie
def datasourceentryiface(request):
    message = ''
    if request.method != 'GET': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    dsentrydict = {}
    ifacedict = {}
    colllist = []
    for element in COLLECTIONS:
        colllist.append(element)
    ifacedict['indexes'] = colllist
    metricsdict = {'metrics' : {}}
    for element in COLLECTIONS:
        indxkey = element
        m = metricsdict['metrics']
        if element == "coinmarketcapdata":
            m[indxkey] = METRICS_COINMARKETCAPDATA
        elif element == "coinmarketdata":
            m[indxkey] = METRICS_COINMARKETDATA
        elif element == "investdata":
            m[indxkey] = METRICS_INVESTDATA
        elif element == "ohlcvdata":
            m[indxkey] = METRICS_OHLCVDATA
        elif element == "coinbase":
            m[indxkey] = METRICS_COINBASE
        else:
             pass # We don't consider any other currency now.
    metricsdict['metrics'] = m
    ifacedict['metricsdict'] = metricsdict
    ifacedict['urlprefix'] = utils.gethosturl(request)
    csrf_token = get_token(request)
    #tmpl = get_template("dsentry.html")
    ifacedict.update(csrf(request))
    cxt = RequestContext(request, ifacedict)
    #for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
    #    dsentryhtml = dsentryhtml.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
    #dsentryhtml = tmpl.render(cxt)
    rtr = render_to_response("dsentry.html", ifacedict, context_instance=cxt)
    return rtr


@csrf_protect
def visualize_investdb_currencyprice(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.investdata.find()
    record = []
    datadict = {}
    for rec in data:
        record.append(rec)
    datadict['investdata'] = record
    currency_vals = {}
    currency_times = {}
    max_cols = 0
    register_matplotlib_converters()
    for valdict in datadict['investdata']:
        currname = valdict['currency_name']
        val = valdict['currency_price']
        val = re.sub('[^0-9]', '', val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = currency_vals[currname]
            data.append(val)
            currency_vals[currname] = data
            dtlist = currency_times[currname]
            dtlist.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_cols:
                max_cols = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            max_cols = 1
    datarecs = []
    currlist = []
    currencynames = []
    fig1, ax1 = mlt.subplots()
    for currname in currency_vals.keys():
        currlist.append(currname)
        datarecs.append(currency_vals[currname])
        xrangelist = []
        for dt in currency_times[currname]:
            xrangelist.append(datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M"))
        xs = mdates.date2num(xrangelist)
        ax1.plot(xs, currency_vals[currname])
        currencynames.append(currname)
    mlt.gca().legend(tuple(currencynames))
    mlt.xlabel("Time")
    mlt.ylabel("Currency Price")
    mlt.suptitle("Currency Price vs Time")
    mlt.tick_params(axis='both', labelrotation=90)
    ax1.xaxis_date() # interpret the x-axis values as dates
    fig1.autofmt_xdate()
    #ax.set_ylabel('Currency Price', va='bottom', labelpad=10)
    mlt.savefig('/home/supriyo/work/cryptocurranalysis/cryptocurranalysis/userdata/investdata_currprice.png')
    return HttpResponse("media/investdata_currprice.png")


@csrf_protect
def visualize_investdb_marketcap(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.investdata.find()
    record = []
    datadict = {}
    for rec in data:
        record.append(rec)
    datadict['investdata'] = record
    currency_vals = {}
    currency_times = {}
    max_cols = 0
    register_matplotlib_converters()
    for valdict in datadict['investdata']:
        currname = valdict['currency_name']
        val = valdict['market_cap']
        val = re.sub('[^0-9]', '', val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = currency_vals[currname]
            data.append(val)
            currency_vals[currname] = data
            dtlist = currency_times[currname]
            dtlist.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_cols:
                max_cols = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            max_cols = 1
    datarecs = []
    currlist = []
    currencynames = []
    fig1, ax1 = mlt.subplots()
    for currname in currency_vals.keys():
        currlist.append(currname)
        datarecs.append(currency_vals[currname])
        xrangelist = []
        for dt in currency_times[currname]:
            xrangelist.append(datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M"))
        xs = mdates.date2num(xrangelist)
        ax1.plot(xs, currency_vals[currname])
        currencynames.append(currname)
    mlt.gca().legend(tuple(currencynames))
    mlt.xlabel("Time")
    mlt.ylabel("Market Capitalization")
    mlt.suptitle("Market Capitalization vs Time")
    mlt.tick_params(axis='both', labelrotation=90)
    ax1.xaxis_date()     # interpret the x-axis values as dates
    fig1.autofmt_xdate()
    #ax.set_ylabel('Currency Price', va='bottom', labelpad=10)
    mlt.savefig('/home/supriyo/work/cryptocurranalysis/cryptocurranalysis/userdata/investdata_marketcap.png')
    return HttpResponse("media/investdata_marketcap.png")


@csrf_protect
def visualize_ohlcv_voltraded(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.ohlcvdata.find()
    df = pd.DataFrame(list(data))
    tp_open_index = 0
    by_currency_name = df.groupby('currency_name')
    time_series = []
    volume_traded = []
    currency_names = []
    register_matplotlib_converters()
    for currency_grp in by_currency_name:
        currency_name_ps = currency_grp[1]['currency_name']
        for currname in currency_name_ps:
            currname = re.sub("\d+\s+", "", currname)
            currency_names.append(currname)
            break
        try:
            ts_open_all = currency_grp[1]['time_open']
            time_all = []
            ctr = 0
            for ts_open in ts_open_all:
                print "\n******************* ", ts_open, " ### ", list(currency_grp[1]['volume_traded'])[ctr], " **********************\n"
                ts_open = re.sub('(\:\d{2}\.\d+)Z$', '', str(ts_open))
                ts_open = re.sub('\d+\s+', '', str(ts_open))
                ts_open = re.sub('T', ' ', str(ts_open))
                dt_open = datetime.datetime.strptime(ts_open, "%Y-%m-%d %H:%M")
                time_all.append(dt_open)
                ctr += 1
            time_series.append(time_all)
            volume_traded.append(currency_grp[1]['volume_traded'])
        except:
            pass
    # Now start the plotting for plots!
    fig1, ax1 = mlt.subplots()
    #print time_series.__len__()
    #print volume_traded.__len__()
    j = 0
    for currency_grp in by_currency_name:
        xs = mdates.date2num(time_series[j])
        ax1.plot(xs, volume_traded[j])
        j += 1
    mlt.gca().legend(tuple(currency_names))
    mlt.xlabel("Start Time")
    mlt.ylabel("Volume Traded")
    mlt.suptitle("Volume Traded vs Start Time")
    mlt.tick_params(axis='both', labelrotation=90)
    ax1.xaxis_date()     # interpret the x-axis values as dates
    fig1.autofmt_xdate()
    mlt.savefig('/home/supriyo/work/cryptocurranalysis/cryptocurranalysis/userdata/ohlcv_voltraded.png')
    return HttpResponse("media/ohlcv_voltraded.png")


@csrf_protect
def visualize_ohlcv_priceopen(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.ohlcvdata.find()
    df = pd.DataFrame(list(data))
    tp_open_index = 0
    by_currency_name = df.groupby('currency_name')
    time_series = []
    price_open = []
    currency_names = []
    register_matplotlib_converters()
    for currency_grp in by_currency_name:
        currency_name_ps = currency_grp[1]['currency_name']
        for currname in currency_name_ps:
            currname = re.sub("\d+\s+", "", currname)
            currency_names.append(currname)
            break
        try:
            ts_open_all = currency_grp[1]['time_open']
            ctr = 0
            time_all = []
            for ts_open in ts_open_all:
                ts_open = re.sub('(\:\d{2}\.\d+)Z$', '', str(ts_open))
                ts_open = re.sub('\d+\s+', '', str(ts_open))
                ts_open = re.sub('T', ' ', str(ts_open))
                dt_open = datetime.datetime.strptime(ts_open, "%Y-%m-%d %H:%M")
                time_all.append(dt_open)
            time_series.append(time_all)
            price_open.append(currency_grp[1]['price_open'])
        except:
            pass
    # Now start the plotting for plots!
    fig1, ax1 = mlt.subplots()
    #print time_series.__len__()
    #print volume_traded.__len__()
    j = 0
    for currency_grp in by_currency_name:
        xs = mdates.date2num(time_series[j])
        ax1.plot(xs, price_open[j])
        j += 1
    mlt.gca().legend(tuple(currency_names))
    mlt.xlabel("Start Time")
    mlt.ylabel("Price Open")
    mlt.suptitle("Price Open vs Start Time")
    mlt.tick_params(axis='both', labelrotation=90)
    ax1.xaxis_date()     # interpret the x-axis values as dates
    fig1.autofmt_xdate()
    mlt.savefig('/home/supriyo/work/cryptocurranalysis/cryptocurranalysis/userdata/ohlcv_priceopen.png')
    return HttpResponse("media/ohlcv_priceopen.png")


@csrf_protect
def visualize_ohlcv_priceclose(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.ohlcvdata.find()
    df = pd.DataFrame(list(data))
    tp_open_index = 0
    by_currency_name = df.groupby('currency_name')
    time_series = []
    price_close = []
    currency_names = []
    register_matplotlib_converters()
    for currency_grp in by_currency_name:
        currency_name_ps = currency_grp[1]['currency_name']
        for currname in currency_name_ps:
            currname = re.sub("\d+\s+", "", currname)
            currency_names.append(currname)
            break
        try:
            ts_open_all = currency_grp[1]['time_open']
            ctr = 0
            time_all = []
            for ts_open in ts_open_all:
                ts_open = re.sub('(\:\d{2}\.\d+)Z$', '', str(ts_open))
                ts_open = re.sub('\d+\s+', '', str(ts_open))
                ts_open = re.sub('T', ' ', str(ts_open))
                dt_open = datetime.datetime.strptime(ts_open, "%Y-%m-%d %H:%M")
                time_all.append(dt_open)
            time_series.append(time_all)
            price_close.append(currency_grp[1]['price_close'])
        except:
            pass
    # Now start the plotting for plots!
    fig1, ax1 = mlt.subplots()
    #print time_series.__len__()
    #print volume_traded.__len__()
    j = 0
    for currency_grp in by_currency_name:
        xs = mdates.date2num(time_series[j])
        ax1.plot(xs, price_close[j])
        j += 1
    mlt.gca().legend(tuple(currency_names))
    mlt.xlabel("Start Time")
    mlt.ylabel("Price Close")
    mlt.suptitle("Price Close vs Start Time")
    mlt.tick_params(axis='both', labelrotation=90)
    ax1.xaxis_date()     # interpret the x-axis values as dates
    fig1.autofmt_xdate()
    mlt.savefig('/home/supriyo/work/cryptocurranalysis/cryptocurranalysis/userdata/ohlcv_priceclose.png')
    return HttpResponse("media/ohlcv_priceclose.png")


@requires_csrf_token
def visualize_ohlcv_pricehigh(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.ohlcvdata.find()
    df = pd.DataFrame(list(data))
    tp_open_index = 0
    by_currency_name = df.groupby('currency_name')
    time_series = []
    price_high = []
    currency_names = []
    register_matplotlib_converters()
    for currency_grp in by_currency_name:
        currency_name_ps = currency_grp[1]['currency_name']
        for currname in currency_name_ps:
            currname = re.sub("\d+\s+", "", currname)
            currency_names.append(currname)
            break
        try:
            ts_open_all = currency_grp[1]['time_open']
            ctr = 0
            time_all = []
            for ts_open in ts_open_all:
                ts_open = re.sub('(\:\d{2}\.\d+)Z$', '', str(ts_open))
                ts_open = re.sub('\d+\s+', '', str(ts_open))
                ts_open = re.sub('T', ' ', str(ts_open))
                dt_open = datetime.datetime.strptime(ts_open, "%Y-%m-%d %H:%M")
                time_all.append(dt_open)
            time_series.append(time_all)
            price_high.append(currency_grp[1]['price_high'])
        except:
            pass
    # Now start the plotting for plots!
    fig1, ax1 = mlt.subplots()
    #print time_series.__len__()
    #print volume_traded.__len__()
    j = 0
    for currency_grp in by_currency_name:
        xs = mdates.date2num(time_series[j])
        ax1.plot(xs, price_high[j])
        j += 1
    mlt.gca().legend(tuple(currency_names))
    mlt.xlabel("Start Time")
    mlt.ylabel("Price High")
    mlt.suptitle("Price High vs Start Time")
    mlt.tick_params(axis='both', labelrotation=90)
    ax1.xaxis_date()     # interpret the x-axis values as dates
    fig1.autofmt_xdate()
    mlt.savefig('/home/supriyo/work/cryptocurranalysis/cryptocurranalysis/userdata/ohlcv_pricehigh.png')
    return HttpResponse("media/ohlcv_pricehigh.png")


@csrf_protect
def visualize_ohlcv_tradescount(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.ohlcvdata.find()
    df = pd.DataFrame(list(data))
    tp_open_index = 0
    by_currency_name = df.groupby('currency_name')
    time_series = []
    trades_count = []
    currency_names = []
    register_matplotlib_converters()
    for currency_grp in by_currency_name:
        currency_name_ps = currency_grp[1]['currency_name']
        for currname in currency_name_ps:
            currname = re.sub("\d+\s+", "", currname)
            currency_names.append(currname)
            break
        try:
            ts_open_all = currency_grp[1]['time_open']
            ctr = 0
            time_all = []
            for ts_open in ts_open_all:
                ts_open = re.sub('(\:\d{2}\.\d+)Z$', '', str(ts_open))
                ts_open = re.sub('\d+\s+', '', str(ts_open))
                ts_open = re.sub('T', ' ', str(ts_open))
                dt_open = datetime.datetime.strptime(ts_open, "%Y-%m-%d %H:%M")
                time_all.append(dt_open)
            time_series.append(time_all)
            trades_count.append(currency_grp[1]['trades_count'])
            #print "\n\n************** ",str(currency_grp[1]['trades_count']), " ### ", str(currency_grp[1]['currency_name']), " ***************\n"
        except:
            pass
    # Now start the plotting for plots!
    fig1, ax1 = mlt.subplots()
    #print time_series.__len__()
    #print volume_traded.__len__()
    j = 0
    for currency_grp in by_currency_name:
        xs = mdates.date2num(time_series[j])
        ax1.plot(xs, trades_count[j])
        j += 1
    mlt.gca().legend(tuple(currency_names))
    mlt.xlabel("Start Time")
    mlt.ylabel("Trades Count")
    mlt.suptitle("Trades Count vs Start Time")
    mlt.tick_params(axis='both', labelrotation=90)
    ax1.xaxis_date()     # interpret the x-axis values as dates
    fig1.autofmt_xdate()
    mlt.savefig('/home/supriyo/work/cryptocurranalysis/cryptocurranalysis/userdata/ohlcv_tradescount.png')
    return HttpResponse("media/ohlcv_tradescount.png")

@csrf_protect
def coinbaseindexdisplay(request):
    if request.METHOD != "POST":
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    return HttpResponse("<img src='https://index-am.coinbase.com/oembed.json?url=https://index-am.coinbase.com/widget/index&maxwidth=500&maxheight=200'>")



