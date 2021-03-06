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
import urllib, urllib2, httplib
import requests

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

ifacedict = {}



def datasourceentryiface(request):
    message = ''
    if request.method != 'GET': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    dsentrydict = {}
    ifacedict = {}
    ifacedict = utils.populate_ifacedict_basic(request)
    colllist = []
    userid = None
    ifacedict['userid'] = ""
    ifacedict['username'] = 'Anonymous'
    if request.COOKIES.has_key('userid'):
        userid = request.COOKIES['userid']
    ifacedict['userid'] = userid
    db = utils.get_mongo_client()
    username = utils.getusernamefromuserid(userid)
    ifacedict['username'] = username
    ifacedict['loggedin'] = '0'
    if utils.isloggedin(request):
        ifacedict['loggedin'] = '1'
    if DEBUG:
        print("IsLoggedIn: " + ifacedict['loggedin'] + "\n")
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
        elif element == "coinlayer":
            m[indxkey] = METRICS_COINLAYER
        else:
            pass # We don't consider any other currency now.
    metricsdict['metrics'] = m
    ifacedict['metricsdict'] = metricsdict
    ifacedict['urlprefix'] = utils.gethosturl(request)
    # Some variables that have been used in HTML, but not processed here.
    ifacedict['prevk'] = 0
    csrf_token = get_token(request)
    ifacedict.update(csrf(request))
    cxt = RequestContext(request)
    rtr = render_to_response("dsentry.html", ifacedict, context_instance=cxt)
    return rtr


@ensure_csrf_cookie
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
    # Some variables that have been used in HTML, but not processed here.
    datadict['prevk'] = 0
    currency_vals = {}
    currency_times = {}
    max_cols = 0
    #register_matplotlib_converters()
    for valdict in datadict['investdata']:
        currname = valdict['currency_name']
        val = valdict['currency_price']
        val = re.sub('[^0-9\.]', '', val)
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
    return HttpResponse("")


@ensure_csrf_cookie
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
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['investdata'] = record
    # Some variables that have been used in HTML, but not processed here.
    ddict['prevk'] = 0
    currency_vals = {}
    currency_times = {}
    max_cols = 0
    #register_matplotlib_converters()
    for valdict in ddict['investdata']:
        currname = valdict['currency_name']
        val = valdict['currency_price']
        val = re.sub('[^0-9\.]', '', val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = currency_vals[currname]
            data.append(val)
            currency_vals[currname] = data
            dtlist = currency_times[currname]
            dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_cols:
                max_cols = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_cols = 1
    datarecs = []
    currlist = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : datarecs[i]})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : datarecs[i]}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Invest DB Currency Price ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
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
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['investdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    for valdict in ddict['investdata']:
        currname = valdict['currency_name']
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict['market_cap']
        bflag = 0
        if utils.billionpattern.search(val):
            bflag = 1
        val = re.sub('[^0-9\.]', '', val)
        val = str(float(val) * 1000) # Converted to Million
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(val)
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
            else:
                currency_times[currname] = dtlist
            dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : datarecs[i]})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : datarecs[i]}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Invest DB Market Capitalization ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def visualize_investdb_vol24hrs(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.investdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['investdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    for valdict in ddict['investdata']:
        currname = valdict['currency_name']
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict['volume_24hr']
        bflag = 0
        if utils.billionpattern.search(val):
            bflag = 1
        val = re.sub('[^0-9\.]', '', val)
        val = str(float(val) * 1000) # Converted to Million
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(val)
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
            else:
                currency_times[currname] = dtlist
            dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : datarecs[i]})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : datarecs[i]}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Volume 24 Hours ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def visualize_investdb_change24hrs(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.investdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['investdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    for valdict in ddict['investdata']:
        currname = valdict['currency_name']
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict['change_24hr']
        bflag = 0
        if utils.billionpattern.search(val):
            bflag = 1
        val = re.sub('[^0-9\.\-]', '', val)
        val = str(float(val) * 1000) # Converted to Million
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(val)
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
            else:
                currency_times[currname] = dtlist
            dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : datarecs[i]})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : datarecs[i]}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Change 24 Hours (Percentage)";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def visualize_investdb_change7days(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.investdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['investdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    for valdict in ddict['investdata']:
        currname = valdict['currency_name']
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict['change_7days']
        bflag = 0
        if utils.billionpattern.search(val):
            bflag = 1
        val = re.sub('[^0-9\.\-]', '', val)
        val = str(float(val) * 1000) # Converted to Million
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(val)
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
            else:
                currency_times[currname] = dtlist
            dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : datarecs[i]})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : datarecs[i]}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Change 7 Days (Percentage)";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def visualize_investdb_totalvolume(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.investdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['investdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    for valdict in ddict['investdata']:
        currname = valdict['currency_name']
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict['total_volume']
        val = re.sub('[^0-9\.\-]', '', val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(val)
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
            else:
                currency_times[currname] = dtlist
            dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : datarecs[i]})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = datarecs[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : datarecs[i]}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Total Volume ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
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
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['ohlcvdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "ETHEREUM CLASSIC", "COSMOS")
    collected_target_currname = {}
    for valdict in ddict['ohlcvdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict['volume_traded']
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['time_period_start'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Total Volume ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
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
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['ohlcvdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "ETHEREUM CLASSIC", "COSMOS")
    collected_target_currname = {}
    for valdict in ddict['ohlcvdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["trades_count"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['time_period_start'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Trades Count ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def visualize_ohlcv_pricehigh(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.ohlcvdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['ohlcvdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "ETHEREUM CLASSIC", "COSMOS")
    collected_target_currname = {}
    for valdict in ddict['ohlcvdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["price_high"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['time_period_start'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Price High ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
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
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['ohlcvdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "ETHEREUM CLASSIC", "COSMOS")
    collected_target_currname = {}
    for valdict in ddict['ohlcvdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["price_open"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['time_open'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Price Open ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
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
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['ohlcvdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "ETHEREUM CLASSIC", "COSMOS")
    collected_target_currname = {}
    for valdict in ddict['ohlcvdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["price_close"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['time_close'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Price Close ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def visualize_ohlcv_pricelow(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.ohlcvdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['ohlcvdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "ETHEREUM CLASSIC", "COSMOS")
    collected_target_currname = {}
    for valdict in ddict['ohlcvdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["price_low"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['time_period_end'] # Need to ensure datetime are sorted. I am putting time_period_end since the exact time at which the lowest price occurred is not specified. The 'time_period_end' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Price Low ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def cmcd_percent24hr(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketcapdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarketcapdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "BITCOIN SV", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "NEO", "COSMOS", "QASH")
    collected_target_currname = {}
    for valdict in ddict['coinmarketcapdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["percent24hr"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted. I am putting time_period_end since the exact time at which the lowest price occurred is not specified. The 'time_period_end' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        datetimeentry = re.sub('T', ' ', datetimeentry)
        datetimeentry = re.sub('\:\d+\.\d+Z?$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
        alldatetimes[d] = str(alldatetimes[d])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "CoinMarketCapData - Percent Change in 24 hours."
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__() - 1)
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response



@ensure_csrf_cookie
@csrf_protect
def cmcd_percent07day(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketcapdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarketcapdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "BITCOIN SV", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "NEO", "COSMOS", "QASH")
    collected_target_currname = {}
    for valdict in ddict['coinmarketcapdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["percent7d"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted. I am putting time_period_end since the exact time at which the lowest price occurred is not specified. The 'time_period_end' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        datetimeentry = re.sub('T', ' ', datetimeentry)
        datetimeentry = re.sub('\:\d+\.\d+Z?$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Percent Change in 7 Days "
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def cmcd_volume(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketcapdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarketcapdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "BITCOIN SV", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "NEO", "COSMOS", "QASH")
    collected_target_currname = {}
    for valdict in ddict['coinmarketcapdata']:
        currname = valdict['currency_name']
        if currname.upper() not in target_currencies:
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["volume"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted. I am putting time_period_end since the exact time at which the lowest price occurred is not specified. The 'time_period_end' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        datetimeentry = re.sub('T', ' ', datetimeentry)
        datetimeentry = re.sub('\:\d+\.\d+Z?$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Volume ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def cmcd_percentchange1hr(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketcapdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarketcapdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "BITCOIN SV", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "NEO", "COSMOS", "QASH")
    collected_target_currname = {}
    for valdict in ddict['coinmarketcapdata']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["percent1hr"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['entrydatetime']
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Percent Change 1 Hour ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def cmcd_currencyprice(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketcapdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarketcapdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "BITCOIN SV", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "NEO", "COSMOS", "QASH")
    collected_target_currname = {}
    for valdict in ddict['coinmarketcapdata']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["currency_price"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['entrydatetime']
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Currency Price ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def cmcd_supply(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketcapdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarketcapdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "BITCOIN SV", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "NEO", "COSMOS", "QASH")
    collected_target_currname = {}
    for valdict in ddict['coinmarketcapdata']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["supply"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['entrydatetime']
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "CoinMarketCapData Supply ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def cmcd_marketcap(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketcapdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarketcapdata'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "BITCOIN SV", "XRP", "TETHER", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "NEO", "COSMOS", "QASH")
    collected_target_currname = {}
    for valdict in ddict['coinmarketcapdata']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["marketcap"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['entrydatetime']
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "CoinMarketCapData MarketCap ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def coinmarket_currency_price(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarket'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "DIGIBYTE", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "COSMOS", "DASH", "ZILLIQA")
    collected_target_currname = {}
    for valdict in ddict['coinmarket']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["currency_price"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['last_updated'] # Need to ensure datetime are sorted. I am putting time_period_end since the exact time at which the lowest price occurred is not specified. The 'time_period_end' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Currency Price ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def coinmarket_percent_change_24hr(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarket'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "DIGIBYTE", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "COSMOS", "DASH", "ZILLIQA")
    collected_target_currname = {}
    for valdict in ddict['coinmarket']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["percent_change_24hr"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['last_updated'] # Need to ensure datetime are sorted. I am putting time_period_end since the exact time at which the lowest price occurred is not specified. The 'time_period_end' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Percentage Change in 24 Hours ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def coinmarket_percent_change_1hr(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarket'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "DIGIBYTE", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "COSMOS", "DASH", "ZILLIQA")
    collected_target_currname = {}
    for valdict in ddict['coinmarket']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["percent_change_1hr"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['last_updated'] # Need to ensure datetime are sorted. I am putting time_period_end since the exact time at which the lowest price occurred is not specified. The 'time_period_end' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Percentage Change in 1 Hour ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def coinmarket_volume_24hr(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarket'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "DIGIBYTE", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "COSMOS", "DASH", "ZILLIQA")
    collected_target_currname = {}
    for valdict in ddict['coinmarket']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        val = valdict["volume_24hr"]
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        datetimeentry = valdict['last_updated'] # Need to ensure datetime are sorted. I am putting time_period_end since the exact time at which the lowest price occurred is not specified. The 'time_period_end' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Volume Traded in 24 Hours ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def coinmarket_percent_change_7days(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinmarketdata.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinmarket'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies = ("EOS", "BITCOIN", "BINANCE COIN", "LITECOIN", "XRP", "DIGIBYTE", "STELLAR", "BITCOIN CASH", "ETHEREUM", "MONERO", "COSMOS", "DASH", "ZILLIQA")
    collected_target_currname = {}
    for valdict in ddict['coinmarket']:
        currname = valdict['currency_name']
        if DEBUG:
            print currname, "\n"
        if currname.upper() not in target_currencies:
            if DEBUG:
                print "Curency named '%s' not found"%currname.upper()
            continue
        for k in utils.hexcodecharmap.keys():
            currname = currname.replace(k, utils.hexcodecharmap[k])
        datetimeentry = valdict['last_updated'] # Need to ensure datetime are sorted. I am putting 'last_updated' since the exact time at which the lowest price occurred is not specified. The 'last_updated' is a better candidate for this than time_period_start. (or so I think). Suggestions are welcome.
        if DEBUG:
            print type(datetimeentry), "\n ############################################## \n"
        datetimeentry = re.sub('\:\d+\.\d+Z$', '', datetimeentry)
        datetimeentry = re.sub('T', ' ', datetimeentry)

        val = valdict["percent_change_7days"]
        if DEBUG:
            print val, "\n ###########################################22\n"
        val = re.sub('[^0-9\.\-e]', '', str(val))
        patval = re.compile("(\d+\.?\d*)e?\-?(\d*)")
        patmatchobj = patval.search(val)
        if val == '':
            val = 0.0
        if patmatchobj and patmatchobj.groups().__len__() > 1 and patmatchobj.groups()[1] != '':
            val = re.sub(patval, str(float(patmatchobj.groups()[0])/10 ** int(patmatchobj.groups()[1])), val)
        else:
            val = re.sub(patval, str(float(patmatchobj.groups()[0])), val)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            data.append(float(val))
            currency_vals[currname] = data
            dtlist = list([])
            if currency_times.has_key(currname):
                dtlist = currency_times[currname]
                dtlist.append(datetimeentry)
            else:
                dtlist.append(datetimeentry)
            alldatetimes.append(datetimeentry)
            currency_times[currname] = dtlist
            l = data.__len__()
            if l > max_rows:
                max_rows = l
        else:
            currency_vals[currname] = [val,]
            currency_times[currname] = [datetimeentry, ]
            alldatetimes.append(datetimeentry)
            max_rows = 1
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}
    for currname in currency_vals.keys():
        currname = currname.replace('&#39;', utils.hexcodecharmap['&#39;'])
        datarecs = currency_vals[currname]
        datelists = currency_times[currname]
        currencynames.append(currname)
        for i in range(datarecs.__len__()):
            if datadict.has_key(currname):
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname].append({datelists[i] : float(datarecs[i])})
            else:
                datelists[i] = datelists[i].replace('&#39;', utils.hexcodecharmap['&#39;'])
                datarecs[i] = str(datarecs[i]).replace('&#39;', utils.hexcodecharmap['&#39;'])
                datadict[currname] = [{datelists[i] : float(datarecs[i])}, ]
    for d in range(alldatetimes.__len__()):
        alldatetimes[d] = alldatetimes[d].replace('&#39;', utils.hexcodecharmap['&#39;'])
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Percentage Change 7 Days ";
    ifacedict['currencynames'] = currencynames
    ifacedict['datetimeslist'] = alldatetimes # ALL DISTINCT DATETIMES OF ALL CURRENCIES ARE CONSIDERED.
    colors = utils.randomcolorgenerator(currencynames.__len__())
    ifacedict['colors'] = colors
    ifacedict = json.dumps(ifacedict)
    response = HttpResponse(ifacedict)
    return response


@ensure_csrf_cookie
@csrf_protect
def coinlayer_data(request):
    if request.method != "POST":
        print "method not post"
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    # Access the mongo db with pymongo
    db = utils.get_mongo_client()
    data = db.coinlayer.find()
    record = []
    ddict = {}
    alldatetimes = []
    for rec in data:
        record.append(rec)
    ddict['coinlayer'] = record
    currency_vals = {}
    currency_times = {}
    max_rows = 0
    target_currencies_list = ["BNB","BTC","EOS","LTC","XRP","ETH","BCH","ETC","XMR","XLM","BTG","NEO"]
    ctr = 0
    layerdatetimestr_last = "01-01-1970 00:00:00"
    layerdatetimeobj_last = datetime.datetime.strptime(layerdatetimestr_last, "%d-%m-%Y %H:%M:%S")
    latest3datetimes = []
    for i in range(COINLAYER_NUM_DATETIMES):
        latest3datetimes.append(layerdatetimeobj_last)
    alldatetimeslist = []
    while ctr < record.__len__():
        layerdatetimestr = str(record[ctr]['currdatetime'])
        layerdatetimestr_parts = layerdatetimestr.split(".")
        layerdatetimeobj = datetime.datetime.strptime(layerdatetimestr_parts[0], "%Y-%m-%d %H:%M:%S")
        alldatetimeslist.append(layerdatetimeobj)
        ctr += 1
    alldatetimeslist.sort()
    docdict = {}
    for dtime in alldatetimeslist[:3]:
        dtimestr = dtime.strftime("%Y-%m-%d %H:%M:%S")
        pat = re.compile("^\d{4}\-\d{2}\-\d{2}\s+\d{2}:\d{2}:\d{2}")
        doccursor = db.coinlayer.find({'currdatetime' : {'$regex' : pat}})
        currdict = {}
        cursorlist = []
        for docres in doccursor:
            cursorlist.append(docres)
        for doc in cursorlist:
            for dockey in doc.keys():
                if doc.has_key('BTC'):
                    currdict['Bitcoin'] = str(doc['BTC'])
                if doc.has_key('NEO'):
                    currdict['NEO'] = str(doc['NEO'])
                if doc.has_key('XLM'):
                    currdict['Stellar'] = str(doc['XLM'])
                if doc.has_key('BCH'):
                    currdict['Bitcoin Cash'] = str(doc['BCH'])
                if doc.has_key('EOS'):
                    currdict['EOS'] = str(doc['EOS'])
                if doc.has_key('ETH'):
                    currdict['Ethereum'] = str(doc['ETH'])
                if doc.has_key('XRP'):
                    currdict['Ripple'] = str(doc['XRP'])
                if doc.has_key('BTG'):
                    currdict['Bitcoin Gold'] = str(doc['BTG'])
                if doc.has_key('LTC'):
                    currdict['Litecoin'] = str(doc['LTC'])
                if doc.has_key('BNB'):
                    currdict['Binance Coin'] = str(doc['BNB'])
                if doc.has_key('XMR'):
                    currdict['Monero'] = str(doc['XMR'])
                if doc.has_key('ETC'):
                    currdict['Ethereum Classic'] = str(doc['ETC'])
                else:
                    pass # Unrecognized currency in this scheme.
        docdict[dtimestr] = currdict
        if DEBUG:
            print docdict,"\n"
        docdictjson = json.dumps(docdict)
    return HttpResponse(docdictjson)


@ensure_csrf_cookie
@csrf_protect
@utils.is_session_valid
@utils.session_location_match
def operations(request):
    if request.method != "GET":
        print "method not get"
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    """
    Provide the user to operate on a dashboard for transactions, analysis, research, etc.
    """
    if DEBUG:
        print("In operations....\n")
    userid = request.COOKIES["userid"]
    db = utils.get_mongo_client()
    rec = db["users"].find({'userid' : userid})
    if rec:
        username = rec[0]['username']
    else:
        username = "Anonymous"
    ifacedict = utils.populate_ifacedict_basic(request)
    prof_img_tag = ifacedict['profile_image_tag']
    #urlprefix = utils.gethosturl(request)
    #return HttpResponse("You are logged in successfully as '%s'! %s | <a href='#/' onClick='signout(\"%s\", \"\");'>"%(username, prof_img_tag, userid))
    #return HttpResponse("You are logged in successfully as '%s'! %s"%(username, prof_img_tag))
    return HttpResponse("You are logged in successfully as '%s'!"%username)



# ======================== Blockcypher API calls ============================= #

def get_blockcypher_private_public_keys_address():
    api_endpoint = BLOCKCYPHER_ADDRESS_ENDPOINT
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), utils.NoRedirectHandler())
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : BLOCKCYPHER_HOST }
    postdummydata = "dummy=1"
    blockcypher_request = urllib2.Request(api_endpoint, postdummydata, http_headers) # Need to put the dummy data to treat it as POST request.
    blockcypher_response = None
    try:
        blockcypher_response = opener.open(blockcypher_request)
    except:
        print "Could not get the blockcypher address data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    if not blockcypher_response:
        print "Could not retrieve response from the request to '%s'\n"%BLOCKCYPHER_ADDRESS_ENDPOINT
        return False
    blockcypher_data_json = blockcypher_response.read()
    if DEBUG:
        print(blockcypher_data_json)
    return blockcypher_data_json


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def create_wallet(request):
    """
    A user can have more than one wallet for the same currency under his/her name.
    Each of these wallets will have a different name (provided by the user) and an
    address (created during the address creation process using the method named
    'get_blockcypher_private_public_keys_address'. The address needs to be unique
    in the collection, but the name may be used by other users (with other addresses)
    having one or more wallets.
    """
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "msg:err:Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    db = utils.get_mongo_client()
    rec = db["users"].find({'userid' : userid})
    username = None
    hdwallet = '0' # By default, you create a normal wallet. If you want to create an HD wallet, you need to check the checkbox in the interface.
    if rec:
        username = rec[0]['username']
    if not username:
        message = "msg:err:Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('currency_name'):
        currencyname = request.POST['currency_name']
    else:
        message = "msg:err:The currency name field is mandatory. You have not entered a currency name. Please select a currency name and try again"
        response = HttpResponse(message)
        return response
    if DEBUG:
        print("Currency Name: %s\n"%currencyname)
    if request.POST.has_key('hdwallet'):
        hdwallet = request.POST['hdwallet']
    else:
        message = "We are going to create an HD Wallet here."
    allowed = utils.check_wallet_limits(userid)
    if not allowed:
        message = "You cannot create a new wallet without upgrading your membership. Please <a href='#/' onclick='javascript:upgrademembership();'>upgrade</a> and try again"
        response = HttpResponse(message)
        return response
    allowed = utils.check_currency_limits(userid, currencyname)
    if not allowed:
        message = "You cannot create a new wallet for this currency without upgrading your membership. Please <a href='#/' onclick='javascript:upgrademembership();'>upgrade</a> and try again"
        response = HttpResponse(message)
        return response
    if request.POST.has_key('walletname'):
        walletname = request.POST['walletname']
    else:
        message = "msg:err:The wallet name field is mandatory. You have not entered a wallet name. Please enter a wallet name and try again"
        response = HttpResponse(message)
        return response
    v = utils.validate_wallet_name(walletname)
    if not v:
        message = "msg:err:Your wallet name is not valid. Please modify it as per the rules mentioned below to make it a valid one.<br>"
        message += utils.rules_valid_name()
        response = HttpResponse(message)
        return response
    blockcypher_data_json = get_blockcypher_private_public_keys_address()
    blockcypher_data = json.loads(blockcypher_data_json)
    private, public, address, wif = "", "", "", ""
    if blockcypher_data.has_key('private'):
        private = blockcypher_data['private']
    if blockcypher_data.has_key('public'):
        public = blockcypher_data['public']
    if blockcypher_data.has_key('address'):
        address = blockcypher_data['address']
    if blockcypher_data.has_key('wif'):
        wif = blockcypher_data['wif'] # Wallet Import Format - a common encoding for the private key
    if request.POST.has_key('address') and request.POST["address"] != "":
        address = request.POST["address"]
    if request.POST.has_key('publickey') and request.POST["publickey"] != "":
        public = request.POST["publickey"]
    if request.POST.has_key('wif') and request.POST["wif"] != "":
        wif = request.POST["wif"]
    if DEBUG:
        print("Address: %s\n"%address);
        print("Public: %s\n"%public);
        print("private: %s\n"%private);
        print("wif: %s\n"%wif);
    if not private or not public or not address or not wif:
        message = "msg:err:Could not retrieve all the data to create a wallet. Please try again after some time." # TODO: Need to tell user what to do if it keeps failing
        response = HttpResponse(message)
        return response
    # Create the wallet for the user and put it in the DB in the 'wallets' collection.
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : BLOCKCYPHER_HOST }
    postdata = {'name' : walletname, 'addresses' : [address]}
    postdatastr = json.dumps(postdata)
    lcurrname = currencyname.lower()
    if lcurrname == "btc":
        if hdwallet == '0' or not hdwallet:
            api_endpoint = "https://api.blockcypher.com/v1/btc/main/wallets?token=" + BLOCKCYPHER_ACCOUNT_TOKEN
        else:
            api_endpoint = "https://api.blockcypher.com/v1/btc/main/wallets/hd?token=" + BLOCKCYPHER_ACCOUNT_TOKEN
        if DEBUG:
            print("API Endpoint: %s\n"%api_endpoint)
        opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), utils.NoRedirectHandler())
        blockcypher_request = urllib2.Request(api_endpoint, postdatastr, http_headers)
        blockcypher_response = None
        try:
            blockcypher_response = opener.open(blockcypher_request)
        except:
            print "msg:err:Could not get the blockcypher wallet data - Error= %s\n"%sys.exc_info()[1].__str__()
            message = "msg:err:Could not get the blockcypher wallet data - Error= %s\n"%sys.exc_info()[1].__str__()
            response = HttpResponse(message)
            return response
        if not blockcypher_response:
            print "msg:err:Could not retrieve response from the request to '%s'\n"%api_endpoint
            message = "msg:err:Could not retrieve response from the request to '%s'\n"%api_endpoint
            response = HttpResponse(message)
            return response
        blockcypher_data_json = blockcypher_response.read()
        if DEBUG:
            print(blockcypher_data_json)
    elif lcurrname == "eth": #Blockcypher will handle it. Note, Ethereum wallets are basically addresses with cryptographic pair of keys.
        # curl -sX POST https://api.blockcypher.com/v1/eth/main/addrs?token=37315496914d40a49c48316595b5e392
        message = "msg:err:Create Wallet not implemented for this currency as yet"
        return HttpResponse(message)
    elif lcurrname == "ltc": # Need to handle these too. With CryptoAPIs.io
        apikey = CRYPTOAPIS_KEY_VALUE
        keyname = CRYPTOAPIS_KEY_NAME
        message = "msg:err:Create Wallet not implemented for this currency as yet"
        return HttpResponse(message)
    else:
        message = "msg:err:Create Wallet not implemented for this currency as yet"
        return HttpResponse(message)
    # At this point, the wallet has been created, and we can store that in our DB with key pair and address associated with it.
    db = utils.get_mongo_client()
    timenow = datetime.datetime.now()
    dtimestr = timenow.strftime("%Y-%m-%d %H:%M:%S")
    insertd = {'userid' : userid, 'username' : username, 'currencyname' : currencyname.lower(), 'balance_amt' : 0, 'last_updation' : dtimestr, 'wallet_address' : address, 'public_key' : public, 'wif' : wif, 'wallet_name' : walletname}
    try:
        db.wallets.insert_one(insertd) # TODO: Dillema as to whether to store the private key in the DB or not.
    except:
        message = "msg:err:Couldn't create the wallet - Error: %s\n"%sys.exc_info()[1].__str__()
        response = HttpResponse(response)
        return response
    message = "Your wallet was created successfully. Please make a note of the following:<br />Public Key: %s<br />Private Key: %s<br />Address: %s<br />Wallet Name: %s<br />"%(public, private, address, walletname)
    message += "<br />Please also note that we are NOT going to store the private key in our database. It is your responsibility to store it at a safe location. You will need it during transactions and trading, and during those operations you would be asked to provide your private key so that we may process your requests.<br />If you lose your private key, you basically lose your wallet.<br />Please also make a note of all the parameters shown above."
    response = HttpResponse(message)
    return response


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def address_add_to_wallet_form(request):
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    db = utils.get_mongo_client()
    rec = db["users"].find({'userid' : userid})
    username = None
    if rec:
        username = rec[0]['username']
    if not username:
        message = "Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    userwalletsrecs = db.wallets.find({'userid' : userid})
    walletnames = {} # We will need unique wallet names for the user. Note that the user can have more than one wallet with the same name with different addresses.
    for userwallet in userwalletsrecs:
        walletname = userwallet['wallet_name']
        if not walletnames.has_key(walletname):
            walletnames[walletname] = 1
        else:
            pass
    # Get addresses now
    useraddressrecs = db.address.find({'userid' : userid})
    useraddresses = {} # This can be a list as there can't be multiple addresses with the same address field.
    for useraddress in useraddressrecs:
        address = useraddress['address']
        publickey = useraddress['publickey']
        wif = useraddress['wif']
        composite_element = address + "##" + publickey + "##" + wif
        useraddresses[address] = composite_element
    ifacedict = utils.populate_ifacedict_basic(request)
    ifacedict['useraddresses'] = useraddresses
    ifacedict['walletnames'] = walletnames.keys()
    ifacedict.update(csrf(request))
    cxt = RequestContext(request)
    rtr = render_to_response("add_address_to_wallet.html", ifacedict, context_instance=cxt)
    return rtr


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def add_addresses_to_wallet(request):
    """
    This method adds an address to an existing wallet owned by the user. 
    In order to add an address to an existing wallet, the wallet name
    is sent as one of the POST arguments. A successful operation would
    create a new document in the 'wallets' collection in the DB.
    """
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if DEBUG:
        print("user id is %s\n"%userid)
    if not userid:
        message = "Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    db = utils.get_mongo_client()
    rec = db["users"].find({'userid' : userid})
    username = None
    if rec:
        username = rec[0]['username']
    if not username:
        message = "Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    if DEBUG:
        print("username is %s\n"%username)
    walletname, addresses = "", ""
    if request.POST.has_key('selwallet'):
        walletname = request.POST['selwallet']
        if utils.isStringEmpty(walletname):
            message = "The required parameter 'walletname' cannot be empty. Please specify the wallet name at the appropriate field on the form and try again."
            response = HttpResponse(message)
            return response
        walletname = walletname.strip()
    else:
        message = "The required parameter 'selwallet' couldn't be found. Please specify the wallet name at the appropriate field on the form and try again."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('seladdress'):
        addresses = request.POST['seladdress']
        addresses = addresses.strip()
        if utils.isStringEmpty(addresses) and addresses.find(",") == -1:
            message = "The required parameter 'seladdress' cannot be empty. Please specify the addresses you want to add to the wallet at the appropriate field on the form and try again."
            response = HttpResponse(message)
            return response
    else:
        message = "The required parameter 'seladdress' couldn't be found. Please specify the addresses you want to add to your wallet at the appropriate field on the form and try again."
        response = HttpResponse(message)
        return response
    if DEBUG:
        print(str(type(addresses)) + "\n=============== \n")
    addresses_list = addresses.split(",")
    if DEBUG:
        print("Addresses submitted is %s\n"%('\n'.join(addresses_list)))
    # Now check if the wallet exist in our DB and it is owned by the user specified using the username.
    db = utils.get_mongo_client()
    recwlt = db.wallets.find({'username' : username, 'wallet_name' : walletname})
    currencyname, balance_amt, public_key, wif, dtimestr = "btc", "", "", "",""
    if not recwlt or recwlt.count < 1:
        message = "It seems that you have specified a wrong wallet name. Either the wallet doesn't exist or you are not the owner of the wallet. Kindly rectify your mistake and try again."
        response = HtpResponse(message)
        return response
    else:
        if DEBUG:
            print("Wallet with name %s exists.\n"%walletname)
        currencyname = recwlt[0]['currencyname']
        balance_amt = 0 # This is for the wallet with the new address. Note that the same wallet can have a balance > 0 with other addresses.
        if DEBUG:
            print("\nCurrency name: %s\n"%currencyname)
        successmessage = ""
        timenow = datetime.datetime.now()
        dtimestr = timenow.strftime("%Y-%m-%d %H:%M:%S")
        opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), utils.NoRedirectHandler())
        # Check if the address(es) is/are already associated with the wallet or not.
        for addr in addresses_list:
            newaddr, publickey, wif = addr.split("##") # These 3 entries are sent from the form in this format:addr##publickey##wif
            if DEBUG:
                print("Address part is %s\n"%newaddr)
            recwallet = db.wallets.find({'username' : username, 'wallet_name' : walletname, 'wallet_address' : newaddr})
            if recwallet and recwallet.count() < 1:
                qset = {'userid' : userid, 'username' : username, 'currencyname' : currencyname.lower(), 'balance_amt' : balance_amt, 'last_updation' : dtimestr, 'wallet_address' : newaddr, 'public_key' : publickey, 'wif' : wif, 'wallet_name' : walletname}
		# HERE, CHECK IF THE USER IS OF THE RIGHT TYPE (GENERAL,SILVER,ETC.) TO DO THIS OPERATION.
                recusr = db.users.find({'userid' : userid})
                usertype = '0' # GENERAL, by default
                if not recusr or recusr.count() < 1:
                    message = "Couldn't find user with the given user Id.\n"
                    response = HttpResponse(message)
                    return response
                else:
                    if recusr[0].has_key('usertype'):
                        usertype = recusr[0]['usertype']
                    else:
                        usertype = '0' # By default, you are a 'general' member.
                memtype = REVERSE_MEMBERSHIP_TYPES[usertype]
                addresslimit = NUM_ADDRESSES_PER_WALLET_GENERAL # By default, general membership
                if memtype == "SILVER":
                    addresslimit = NUM_ADDRESSES_PER_WALLET_SILVER
                elif memtype == "GOLD":
                    addresslimit = NUM_ADDRESSES_PER_WALLET_GOLD
                elif memtype == "PLATINUM":
                    addresslimit = NUM_ADDRESSES_PER_WALLET_PLATINUM
                else:
                    pass
                # Now, send a request with the necessary params to the API hook to keep blockcypher in sync.
                # If we reach here, it means that the named wallet is owned by the user requesting to add the address.
                # Let's oblige her/him. For every address, a new document will be added to the 'wallets' collection.
                # STUPID BLOCKCYPHER CAN USE BTC and ETH ONLY:
                if currencyname.lower() == "btc": # Dumbass blockcypher - doesn't support anything other than bitcoin and ethereum. It says it supports Litecoin, but it practically doesn't. What a looser!!!
                    if recwlt.count() < addresslimit:
                        params = {'token': BLOCKCYPHER_ACCOUNT_TOKEN}
                        api_endpoint = "https://api.blockcypher.com/v1/btc/main/wallets/%s/addresses"%(walletname)
                        postdata = {'addresses' : [newaddr]}
                        r = requests.post(api_endpoint, json=postdata, params=params, verify=True, timeout=BLOCKCYPHER_REQUEST_TIMEOUT)
                        blockcypher_response_dict = utils.get_valid_json(r)
                        if DEBUG:
                            print(blockcypher_response_dict)
                        if blockcypher_response_dict.has_key('token') and blockcypher_response_dict['token'] == BLOCKCYPHER_ACCOUNT_TOKEN and blockcypher_response_dict.has_key('name') and blockcypher_response_dict['name'] == walletname and blockcypher_response_dict.has_key('addresses'):
                            successmessage += "<p style='color:#0000AA;font-weight:bold;'>The address (%s) have been added to the wallet successfully.</p>"%newaddr
                        try:
                            db.wallets.insert_one(qset)
                            if DEBUG:
                                print("Address(es) added successfully to the target wallet.")
                        except:
                            message = "msg#|#err#|#Couldn't add the address to the wallet - Error: %s\n"%sys.exc_info()[1].__str__()
                            response = HttpResponse(response)
                            return response
                    else:
                        message = "msg#|#err#|#You cannot add more addresses to this wallet with your membership status. Please <a href='#/' style='color:#000011;font-weight:bold;text-decoration:underline;' onclick='upgrademembership();'>upgrade</a>, or contact the support staff at support@cryptocurry.me if you are a Platinum member.<br />"
                        response = HttpResponse(message)
                        return response
                elif currencyname.lower() == "eth": # This is handled by blockcypher too. Note, Ethereum wallets are basically just addresses.
                    message = "msg#|#err#|#Process not implemented for this currency as yet"
                    return HttpResponse(message)
                elif currencyname.lower() == "ltc":
                    message = "msg#|#err#|#Process not implemented for this currency as yet"
                    return HttpResponse(message)
                else:
                    message = "msg#|#err#|#Process not implemented for this currency as yet"
                    return HttpResponse(message)
        response = HttpResponse(successmessage)
        return response


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def create_new_address(request):
    """
    This method creates an address and places it in the addresses collection.
    A successful operation would create a new document in the 'addresses'
    collection in the DB.
    """
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    db = utils.get_mongo_client()
    rec = db["users"].find({'userid' : userid})
    username = None
    if rec:
        username = rec[0]['username']
    if not username:
        message = "Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    # Now create a HTTP(S) request to the address creation endpoint.
    api_endpoint = "https://api.blockcypher.com/v1/btc/main/addrs"
    addr_type = "btc"
    encoded_data = "" # Empty POST parameters.
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : BLOCKCYPHER_HOST }
    blockcypher_request = urllib2.Request(api_endpoint, encoded_data, http_headers)
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), utils.NoRedirectHandler())
    blockcypher_response = None
    try:
        blockcypher_response = opener.open(blockcypher_request)
    except:
        print "Could not add the blockcypher addresses data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    if not blockcypher_response:
        print "Could not retrieve response from the request to '%s'\n"%api_endpoint
        return False
    blockcypher_response_json = blockcypher_response.read()
    blockcypher_response_dict = json.loads(blockcypher_response_json)
    if blockcypher_response_dict.has_key('private') and  blockcypher_response_dict.has_key('public') and blockcypher_response_dict.has_key('address'):
        privatekey = blockcypher_response_dict['private']
        publickey = blockcypher_response_dict['public']
        address = blockcypher_response_dict['address']
        wif = blockcypher_response_dict['wif']
        blockcyphertoken = BLOCKCYPHER_ACCOUNT_TOKEN
        timenow = datetime.datetime.now()
        ts = time.time()
        dtimestr = timenow.strftime("%Y-%m-%d %H:%M:%S")
        insertd = {'userid' : userid, 'username' : username, 'address' : address, 'publickey' : publickey, 'created' : dtimestr, 'wif' : wif, 'timestamp' : str(int(ts)), 'addrtype' : addr_type}
        try:
            db.address.insert_one(insertd) # TODO: Dillema as to whether to store the private key in the DB or not. (Right now, we don't store the private key in our DB).
        except:
            message = "msg:err:Couldn't create the address - Error: %s\n"%sys.exc_info()[1].__str__()
            response = HttpResponse(response)
            return response
        message = blockcypher_response_json
        if DEBUG:
            print(message)
        response = HttpResponse(message)
        return response
    else:
        message = "For some reason, the address creation request failed. Please try again. If the error persists, please contact the support staff with the details at support@cryptocurry.me"
        response = HttpResponse(message)
        return response


# ======================== Blockchain calls end here ============================ #
@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def showwalletspage(request):
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<div style='color:#AA0000;'>Either you are not logged in or your session has been corrupted. Please login and try again.</div>"
        response = HttpResponse(message)
        return response
    useridarg = ""
    if request.POST.has_key('userid'):
        useridarg = request.POST['userid']
    else:
        message = "<div style='color:#AA0000;'>Invalid request: No userid was sent as parameter.</div>"
        response = HttpResponse(message)
        return response
    tmpl = get_template("wallets.html")
    rules = utils.rules_valid_name()
    c = {'rules' : rules}
    c.update(csrf(request))
    cxt = Context(c)
    menuitems = tmpl.render(cxt)
    message = "<div id='menuitems' class='menuitems'>" + menuitems + "</div>"
    if userid != useridarg:
        message = "<div style='color:#AA0000;'>Getting conflicting user Ids in request. Please refresh the screen and try again</div>"
        response = HttpResponse(message)
        return response
    db = utils.get_mongo_client()
    rec = db.wallets.find({'userid' : useridarg})
    if not rec or rec.count() < 1:
        message += "<div style='color:#AA0000;'>You do not have any wallet as yet.</div>"
        response = HttpResponse(message)
        return response
    message += "<div style='color:#0000AA;' id='walletslist'>You have the following wallets:<br />"
    walletsdict = {}
    for r in rec:
        walletname = r["wallet_name"]
        currency = r["currencyname"]
        if walletsdict.has_key(walletname):
            continue
        else:
            walletsdict[walletname] = currency
        message += "<a href='#/' onClick=\"javascript:showwalletdetails('%s', '%s');\" style='color:#0000AA;font-weight:bold;'>%s (%s)</a><br />"%(userid, walletname, walletname, currency)
    message += "</div>"
    response = HttpResponse(message)
    return response


def getwalletdetails(request):
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "Either you are not logged in or your session has been corrupted. Please login and try again."
        response = HttpResponse(message)
        return response
    useridarg = ""
    if request.POST.has_key('userid'):
        useridarg = request.POST['userid']
    else:
        message = "Invalid request: No userid was sent as parameter."
        response = HttpResponse(message)
        return response
    if userid != useridarg:
        message = "Getting conflicting user Ids in request. Please refresh the screen and try again"
        response = HttpResponse(message)
        return response
    walletname = ""
    if request.POST.has_key('walletname'):
        walletname = request.POST['walletname']
    else:
        message = "The name of the wallet to query was not found. Please contact the support staff with the userid '%s' and wallet name '%s' at support@cryptocurry.me"%(userid, walletname)
        response = HttpResponse(message)
        return response
    db = utils.get_mongo_client()
    rec = db.wallets.find({'userid' : userid, 'wallet_name' : walletname})
    if not rec or rec.count() < 1:
        message = "Details pertaining to the mentioned wallet couldn't be found. For more information, contact support with userId '%s' and wallet name '%s' at support@cryptocurry.me"%(userid, walletname)
        response = HttpResponse(message)
        return response
    walletdict = {}
    for r in rec:
        currname = r["currencyname"]
        balance_amt = r["balance_amt"]
        walletaddr = r["wallet_address"]
        public_key = r["public_key"]
        last_updation = r["last_updation"]
        wif = r["wif"]
        l = [currname, balance_amt, walletaddr, public_key, last_updation, wif]
        walletdict[walletaddr] = l
    walletdictstr = json.dumps(walletdict)
    return HttpResponse(walletdictstr)


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def upgrademembership(request):
    pass


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def delete_addr_from_wallet(request):
    """
    This method helps display the deletion screen for all currencies.
    """
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<span id='sessterm' style='color:#AA0000;font-weight:bold;'>Either you are not logged in or your session has been corrupted. Please login and try again.</span>"
        response = HttpResponse(message)
        return response
    tmpl = get_template("delete_addr_from_wallet.html")
    c = {'userid' : userid }
    c['hosturl'] = utils.gethosturl(request)
    # FIND OUT ALL WALLETS THIS USER POSSESSES
    db = utils.get_mongo_client()
    rec = db.wallets.find({'userid' : userid})
    if not rec or rec.count() < 1:
        message = "<span style='color:#AA0000;font-weight:bold'>This user doesn't have any wallets</span>"
        return HttpResponse(message)
    allwalletsdict = {}
    walletcurrdict = {}
    for r in rec:
        walletname = str(r['wallet_name'])
        currname = str(r['currencyname'])
        addr = str(r['wallet_address'])
        if allwalletsdict.has_key(walletname):
            addresseslist = allwalletsdict[walletname]
            addresseslist.append(addr)
            allwalletsdict[walletname] = addresseslist
        else:
            allwalletsdict[walletname] = [addr,]
            walletcurrdict[walletname] = currname
    c['walletscurrdict'] = walletcurrdict
    if DEBUG:
        print allwalletsdict
    c['walletsaddrdict'] = allwalletsdict
    c.update(csrf(request))
    cxt = Context(c)
    deladdrfrmwallethtml = tmpl.render(cxt)
    for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
        deladdrfrmwallethtml = deladdrfrmwallethtml.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(deladdrfrmwallethtml)


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def delete_addresses(request):
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<span id='sessterm' style='color:#AA0000;font-weight:bold;'>Either you are not logged in or your session has been corrupted. Please login and try again.</span>"
        response = HttpResponse(message)
        return response
    # Remember to get the address type (currency name/code) by matching the address param in the "address" collection.
    # The 'addrtype' attribute will provide the address type (currency code). If there is no 'addrtype' attribute,
    # then the currency code is "btc" (by default). Now, start by getting the POST parameters.
    # API to hit:https://api.blockcypher.com/v1/<CURRENCY_CODE>/main/wallets/<WALLETNAME>/addresses?token=USERTOKEN&address=<ADDRESSES_VALUES>
    walletname = ""
    if request.POST.has_key('walletname'):
        walletname = request.POST['walletname']
    else:
        message = "<span style='color:#AA0000;font-weight:bold'>The name of the wallet to query was not found. Please contact the support staff with the userid '%s' and wallet name '%s' at support@cryptocurry.me</span>"%(userid, walletname)
        response = HttpResponse(message)
        return response
    addresses = []
    if request.POST.has_key('addresses'):
        addresses_str = request.POST['addresses']
    if ";" in addresses_str:
        addressses = addresses_str.split(";")
    else:
        addresses.append(addresses_str)
    db = utils.get_mongo_client()
    # Make sure the wallet with the given name exists and belongs  to the logged in user
    rec = db.wallets.find({'wallet_name' : walletname, 'userid' : userid})
    if not rec or rec.count() < 1:
        message = "<span style='color:#AA0000;font-weight:bold'>This wallet doesn't exist for the logged in user.</span>"
        return HttpResponse(message)
    # Also check if the wallet contains the given addresses
    validaddresses = {}
    for addr in addresses:
        rec = db.wallets.find({'wallet_name' : walletname, 'wallet_address' : addr, 'userid' : userid})
        if not rec or rec.count() < 1:
            print("The wallet address doesn't exist in the wallets collection for the logged in user")
            continue
        for r in rec:
            validaddresses[addr] = r["currencyname"] # Actually, we expect only one record here.
    # Now validaddresses contains all valid addresses that can be deleted. The keys are the addresses and the values are the address types.
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : BLOCKCYPHER_HOST }
    message = ""
    for vkaddr in validaddresses.keys():
        addrtype = validaddresses[vkaddr]
        if not addrtype:
            addrtype = "btc"
        blockcypher_response = None
        try:
            conn = httplib.HTTPSConnection('api.blockcypher.com')  # Marked as 'https' request.
            conn.request('DELETE', "/v1/%s/main/wallets/%s/addresses?token=%s&address=%s"%(addrtype, walletname, BLOCKCYPHER_ACCOUNT_TOKEN, vkaddr))
            blockcypher_response = conn.getresponse()
            if blockcypher_response.status == 204: # Remove a document from wallets collection
                db.wallets.remove({'wallet_name' : walletname, 'wallet_address' : vkaddr, 'userid' : userid})
                # Also delete any bank account associated with this address
                db.bankaccounts.remove({'walletaddress' : vkaddr, 'walletname' : walletname})
            else:
                if blockcypher_response.status == 404:
                    message += "<span style='color:#AA0000;font-weight:bold'>Could not remove the address from the wallets collection. The address doesn't exist in the given wallet. Please contact support at support@crytocurry.com with the following information: wallet name, address, and username.</span><br />"
                    # Since the address doesn't exist in the wallet for the API, we should delete it from our DB too.
                    db.wallets.remove({'wallet_name' : walletname, 'wallet_address' : vkaddr, 'userid' : userid})
                else:
                    message += "<span style='color:#AA0000;font-weight:bold'>Could not remove the address from the wallets collection. The status code was '%s'. Please contact support at support@crytocurry.com with the following information: wallet name, address, and response status.</span><br />"%(str(blockcypher_response.status))
        except:
            message += "<span style='color:#AA0000;font-weight:bold'>This address could not be removed from the wallet. The error encountered was '%s'.</span><br />"%(sys.exc_info()[1].__str__())
    if len(message) == 0: # No errors were commited during deletion of the given address(es).
        message = "<span style='color:#0000AA;font-weight:bold'>All address(es) were correctly deleted for given wallet. Please note that the address(es) was/were deleted for the specified wallet. The address will continue to exist until you actually delete the address itself.</span>"
    return HttpResponse(message)


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def show_delete_wallet_form(request):
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<span id='sessterm' style='color:#AA0000;font-weight:bold;'>Either you are not logged in or your session has been corrupted. Please login and try again.</span>"
        response = HttpResponse(message)
        return response
    tmpl = get_template("delete_wallet.html")
    c = {'userid' : userid }
    c['hosturl'] = utils.gethosturl(request)
    # FIND OUT ALL WALLETS THIS USER POSSESSES
    db = utils.get_mongo_client()
    rec = db.wallets.find({'userid' : userid})
    if not rec or rec.count() < 1:
        message = "<span style='color:#AA0000;font-weight:bold'>This user doesn't have any wallets <input type='button' name='btnclose' value='Close' onclick='javascript:closethis();'></span>"
        return HttpResponse(message)
    walletcurrdict = {}
    for r in rec:
        walletname = str(r['wallet_name'])
        currname = str(r['currencyname'])
        if not walletcurrdict.has_key(walletname):
            walletcurrdict[walletname] = currname
    c['walletscurrdict'] = walletcurrdict
    c.update(csrf(request))
    cxt = Context(c)
    delwallethtml = tmpl.render(cxt)
    for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
        delwallethtml = delwallethtml.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(delwallethtml)


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def deletewallet(request):
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<span id='sessterm' style='color:#AA0000;font-weight:bold;'>Either you are not logged in or your session has been corrupted. Please login and try again.</span>"
        response = HttpResponse(message)
        return response
    if request.POST.has_key('walletname'):
        walletname = request.POST['walletname']
    else:
        message = "<span style='color:#AA0000;font-weight:bold'>The name of the wallet to query was not found. Please contact the support staff with the userid '%s' and wallet name '%s' at support@cryptocurry.me</span>"%(userid, walletname)
        response = HttpResponse(message)
        return response
    currency = "btc"
    db = utils.get_mongo_client()
    if request.POST.has_key("currency"):
        currency = request.POST['currency']
    # API method and endpoint: DELETE https://api.blockcypher.com/v1/<CURRENCY_CODE>/main/wallets/<WALLET_NAME>?token=YOURTOKEN
    message = ""
    try:
        conn = httplib.HTTPSConnection('api.blockcypher.com')  # Marked as 'https' request.
        if DEBUG:
            print("/v1/%s/main/wallets/%s?token=%s"%(currency, walletname, BLOCKCYPHER_ACCOUNT_TOKEN))
        conn.request('DELETE', "/v1/%s/main/wallets/%s?token=%s"%(currency, walletname, BLOCKCYPHER_ACCOUNT_TOKEN))
        blockcypher_response = conn.getresponse()
        resp_msg = blockcypher_response.read()
        if DEBUG:
            print("STATUS CODE: %s\n"%blockcypher_response.status)
        if blockcypher_response.status == 204: # Remove all document satisfying the below condition from wallets collection
            db.wallets.remove({'wallet_name' : walletname, 'userid' : userid})
        else:
            if blockcypher_response.status == 404:
                message += "<span style='color:#AA0000;font-weight:bold'>Could not remove the wallet from the wallets collection. The selected wallet doesn't exist. Please contact support at support@crytocurry.com with the following information: wallet name and username or userid.</span><br />"
                # Since the wallet doesn't exist for the API, we need to delete it from the database at our end
                db.wallets.remove({'wallet_name' : walletname, 'userid' : userid})
            else:
                message += "<span style='color:#AA0000;font-weight:bold'>Could not remove the wallet from the wallets collection. The status code was '%s'. Please contact support at support@crytocurry.com with the following information: wallet name and response status.</span><br />"%(str(blockcypher_response.status))
    except:
        message += "<span style='color:#AA0000;font-weight:bold'>This wallet could not be removed. The error encountered was '%s'.</span><br />"%(sys.exc_info()[1].__str__())
    if len(message) == 0: # No errors were commited during deletion of the given address(es).
        message = "<span style='color:#0000AA;font-weight:bold'>The selected wallet has been permanently deleted. If you think this is a mistake, please contact support@cryptocurry.com immediately. However, as you had been sufficiently warned, we cannot guarantee that this change can be undone.</span>"
    return HttpResponse(message)


## The functions defined below are part of the "transaction" processes.
@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def buysellcrypto(request):
    """
    'buysellcrypto' allows user to either buy or sell a single cryptocurrency 
    using physical currencies (USD, EUR, AUD, INR will be supported as of now.)
    """
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<span id='sessterm' style='color:#AA0000;font-weight:bold;'>Either you are not logged in or your session has been corrupted. Please login and try again.</span>"
        response = HttpResponse(message)
        return response
    currency = "btc"
    db = utils.get_mongo_client()
    if request.POST.has_key("currency"):
        currency = request.POST['currency']
    # List out the user's wallets so that the user can select the wallet from which the tokens may be chosen.
    # The form should also contain a text field where the user can enter a private key. Inform the user that
    # the private key will NOT be stored in our database (for security reasons). There should also be a 'to-
    # address' text field to which the tokens will be sent. As of now, we will be supporting only 'btc'.
    rec = db.wallets.find({'userid' : userid })
    walletaddrsdict = {}
    if not rec or rec.count() < 1:
        message = "<span style='color:#AA0000;font-weight:bold'>This user doesn't have any wallets <input type='button' name='btnclose' value='Close' onclick='javascript:closebuysell();'></span>"
        return HttpResponse(message)
    for r in rec:
        walletname = str(r['wallet_name'])
        address = str(r['wallet_address'])
        if walletname not in walletaddrsdict.keys():
            walletaddrsdict[walletname] = [address, ]
        else:
            addresses = walletaddrsdict[walletname]
            addresses.append(address)
            walletaddrsdict[walletname] = addresses
    tmpl = get_template("buysell.html")
    c = {'userid' : userid }
    c['hosturl'] = utils.gethosturl(request)
    c['walletaddrsdict'] = walletaddrsdict
    c.update(csrf(request))
    cxt = Context(c)
    buysellhtml = tmpl.render(cxt)
    for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
        buysellhtml = buysellhtml.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(buysellhtml)


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def exchangecryptocurrency(request):
    """
    'exchangecryptocurrency' allows user to buy another cryptocurrency with
    whatever cryptocurrency the user possesses. This has nothing to do with
    physical money.
    """
    pass


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def payments(request):
    """
    This operation allows user to buy goods/services using crypto currencies.
    As of now, only a select few organizations (products or services companies)
    recognize cryptocurrency as a valid mode of payment. Expecting this list
    will grow phenomenally in the future.
    """
    pass


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def calculator(request):
    """
    This operation calculates various cryptocurrency values and would let the
    user to know how much money is owned in terms of some other cryptocurrency
    or in terms of physical money (USD, EUR, AUD, INR)
    """
    pass


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def showbankacctscreen(request):
    """
    Display the "Associate Bank Account" Screen.
    """
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<span id='sessterm' style='color:#AA0000;font-weight:bold;'>Either you are not logged in or your session has been corrupted. Please login and try again.</span>"
        response = HttpResponse(message)
        return response
    currency = "btc"
    db = utils.get_mongo_client()
    walletsrecs = db.wallets.find({'userid' : userid})
    walletaccountsdict = {}
    for walletrec in walletsrecs:
        walletname = str(walletrec['wallet_name'])
        if DEBUG:
            print("\nWALLET NAME: " + walletname + "\n")
        walletaddress = str(walletrec['wallet_address'])
        existingaccts = db.bankaccounts.find({'walletaddress' : walletaddress, 'walletname' : walletname, 'valid' : '1'})
        bankname = ""
        branchcode = ""
        acctnumber = ""
        acctholdername = ""
        if existingaccts and existingaccts.count() > 0: # Bank account fields: bankname, accountnumber, acctholdername, branchcode (IFSCode), walletaddress, walletname, lastbalance, lastupdated, lasttransaction, created. lasttransaction and lastupdated will be same if money has been spent from the bank to buy some token(s), but will be different if money has been earned by selling some token(s).
            for existingacct in existingaccts:
                bankname = existingacct['bankname']
                branchcode = existingacct['branchcode']
                acctnumber = existingacct['accountnumber']
                acctholdername = existingacct['acctholdername']
                break
        if walletaccountsdict.has_key(walletname):
            walletaddressdict = walletaccountsdict[walletname]
            walletaddressdict[walletaddress] = [bankname, acctnumber, acctholdername, branchcode]
            walletaccountsdict[walletname] = walletaddressdict
        else:
            walletaccountsdict[walletname] = {walletaddress : [bankname, acctnumber, acctholdername, branchcode]}
    tmpl = get_template("bankaccount.html")
    c = {'userid' : userid }
    supportedbanks = {}
    for bankname in SUPPORTED_BANKS.keys():
        supportedbanks[bankname] = SUPPORTED_BANKS[bankname]
    c['supportedbanks'] = supportedbanks
    c['hosturl'] = utils.gethosturl(request)
    c['walletaccountsdict'] = walletaccountsdict
    c.update(csrf(request))
    cxt = Context(c)
    bankaccount = tmpl.render(cxt)
    for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
        bankaccount = bankaccount.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(bankaccount)


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def registerbankaccount(request):
    """
    Handle bank account registration.
    """
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<span id='sessterm' style='color:#AA0000;font-weight:bold;'>Either you are not logged in or your session has been corrupted. Please login and try again.</span>"
        response = HttpResponse(message)
        return response
    currency = "btc"
    db = utils.get_mongo_client()
    walletname = request.POST.get('selwalletname', '')
    walletaddress = request.POST.get('walletaddress', '')
    bankname = request.POST.get('bankname', '')
    accountnumber = request.POST.get('acctnumber', '')
    accountname = request.POST.get('acctname', '')
    bankcode = request.POST.get('bankcode', '')
    wltnamemsg = utils.validate_args(walletname, 'wallet_name')
    wltaddrmsg = utils.validate_args(walletaddress, 'wallet_address')
    banknamemsg = utils.validate_args(bankname, 'bank_name')
    acctnomsg = utils.validate_args(accountnumber, 'account_number')
    acctnamemsg = utils.validate_args(accountname, 'account_name')
    bankcodemsg = utils.validate_args(bankcode, 'bank_code')
    wltnamemsgparts = wltnamemsg.split(":")
    wltaddrmsgparts = wltaddrmsg.split(":")
    banknamemsgparts = banknamemsg.split(":")
    acctnomsgparts = acctnomsg.split(":")
    acctnamemsgparts = acctnamemsg.split(":")
    bankcodemsgparts = bankcodemsg.split(":")
    if wltnamemsgparts.__len__() > 2 and wltnamemsgparts[1] == "err":
        message = wltnamemsg
        return HttpResponse(message)
    elif wltaddrmsgparts.__len__() > 2 and wltaddrmsgparts[1] == "err":
        message = wltaddrmsg
        return HttpResponse(message)
    elif banknamemsgparts.__len__() > 2 and banknamemsgparts[1] == "err":
        message = banknamemsg
        return HttpResponse(message)
    elif acctnomsgparts.__len__() > 2 and acctnomsgparts[1] == "err":
        message = acctnomsg
        return HttpResponse(message)
    elif acctnamemsgparts.__len__() > 2 and acctnamemsgparts[1] == "err":
        message = acctnamemsg
        return HttpResponse(message)
    elif bankcodemsgparts.__len__() > 2 and bankcodemsgparts[1] == "err":
        message = bankcodemsg
        return HttpResponse(message)
    # Check if the account already exists in the DB
    existingaccts = db.bankaccounts.find({'walletaddress' : walletaddress, 'walletname' : walletname, 'valid' : '1'})
    if existingaccts and existingaccts.count() > 0:
        if DEBUG:
            print("Number of bank accounts recs: " + str(existingaccts.count()))
        message = "msg:err:An account is already registered for this wallet. Please remove that to add another account."
        return HttpResponse(message)
    # If not registered to the user, add it to the DB. But check the balance in the account first.
    acct_balance = utils.checkaccountbalance(bankname, bankcode, accountnumber, accountname)
    currdatetime = datetime.datetime.now()
    strcurrdatetime = currdatetime.strftime("%Y-%m-%d %H:%M:%S")
    insertd = {'walletaddress' : walletaddress, 'walletname' : walletname, 'bankname' : bankname.lower(), 'branchcode' : bankcode, 'accountnumber' : accountnumber, 'acctholdername' : accountname, 'lastbalance' : str(acct_balance), 'lastupdated' : strcurrdatetime, 'lasttransaction' : '', 'created' : strcurrdatetime, 'valid' : '1'}
    try:
        db.bankaccounts.insert_one(insertd)
    except:
        message = "msg:err:Could not add the bank account. Please contact support@cryptocurry.me with the following error message and your username and bank account information. - Error: %s\n"%sys.exc_info()[1].__str__()
        response = HttpResponse(response)
        return response
    message = "Bank account registered successfully."
    return HttpResponse(message)


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def removebankaccount(request):
    """
    Handle bank account removal.
    """
    if request.method != 'POST':
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    userid = request.COOKIES["userid"]
    if not userid:
        message = "<span id='sessterm' style='color:#AA0000;font-weight:bold;'>Either you are not logged in or your session has been corrupted. Please login and try again.</span>"
        response = HttpResponse(message)
        return response
    currency = "btc"
    db = utils.get_mongo_client()
    walletname = request.POST.get('selwalletname', '')
    walletaddress = request.POST.get('walletaddress', '')
    bankname = request.POST.get('bankname', '')
    accountnumber = request.POST.get('acctnumber', '')
    accountname = request.POST.get('acctname', '')
    bankcode = request.POST.get('bankcode', '')
    """ Why do we need to validate input here??
    wltnamemsg = utils.validate_args(walletname, 'wallet_name')
    wltaddrmsg = utils.validate_args(walletaddress, 'wallet_address')
    banknamemsg = utils.validate_args(bankname, 'bank_name')
    acctnomsg = utils.validate_args(accountnumber, 'account_number')
    acctnamemsg = utils.validate_args(accountname, 'account_name')
    bankcodemsg = utils.validate_args(bankcode, 'bank_code')
    wltnamemsgparts = wltnamemsg.split(":")
    wltaddrmsgparts = wltaddrmsg.split(":")
    banknamemsgparts = banknamemsg.split(":")
    acctnomsgparts = acctnomsg.split(":")
    acctnamemsgparts = acctnamemsg.split(":")
    bankcodemsgparts = bankcodemsg.split(":")
    if wltnamemsgparts.__len__() > 2 and wltnamemsgparts[1] == "err":
        message = wltnamemsg
        return HttpResponse(message)
    elif wltaddrmsgparts.__len__() > 2 and wltaddrmsgparts[1] == "err":
        message = wltaddrmsg
        return HttpResponse(message)
    elif banknamemsgparts.__len__() > 2 and banknamemsgparts[1] == "err":
        message = banknamemsg
        return HttpResponse(message)
    elif acctnomsgparts.__len__() > 2 and acctnomsgparts[1] == "err":
        message = acctnomsg
        return HttpResponse(message)
    elif acctnamemsgparts.__len__() > 2 and acctnamemsgparts[1] == "err":
        message = acctnamemsg
        return HttpResponse(message)
    elif bankcodemsgparts.__len__() > 2 and bankcodemsgparts[1] == "err":
        message = bankcodemsg
        return HttpResponse(message)
    """
    # Try to remove the account from the collection
    try:
        rmvdict = db.bankaccounts.remove({'walletaddress' : walletaddress, 'walletname' : walletname, 'bankname' : bankname.lower(), 'accountnumber' : accountnumber, 'acctholdername' : accountname, 'branchcode' : bankcode})
    except:
        message = "msg:err:The specified bank account doesn't exist. Possibly you have mistyped one or more parameters. Please rectify the mistake to try again. - Error: %s"%sys.exc_info()[1].__str__()
        return HttpResponse(message)
    if rmvdict['n'] > 0:
        message = "Successfully removed the bank account from wallet. Please reopen the overlay screen to view the updated condition of the walet."
    else:
        message = "msg:err:The specified bank account doesn't exist. Possibly you have mistyped one or more parameters. Please rectify the mistake to try again. - Error: %s"%sys.exc_info()[1].__str__()
    return HttpResponse(message)


