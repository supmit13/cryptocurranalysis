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

ifacedict = {}

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
    # Some variables that have been used in HTML, but not processed here.
    ifacedict['prevk'] = 0
    csrf_token = get_token(request)
    ifacedict.update(csrf(request))
    cxt = RequestContext(request, ifacedict)
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
    register_matplotlib_converters()
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
    #for currencyname in datadict.keys():
    #    print "\n\n\n", currencyname, " === ", datadict[currencyname], " \nddd###################################\n "
    ifacedict['datadict'] = datadict
    ifacedict['plotname'] = "Invest DB Currency Price (Figures in USD)";
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
        val = re.sub('[^0-9\.]', '', val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            #print "CURRNAME: ", currname,"\n"
            data.append(val)
            #print "DATA: ", data, "\n"
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
    ifacedict['plotname'] = "Invest DB Market Capitalization (Figures in Billion USD)";
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
        val = re.sub('[^0-9\.]', '', val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            #print "CURRNAME: ", currname,"\n"
            data.append(val)
            #print "DATA: ", data, "\n"
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
    ifacedict['plotname'] = "Volume 24 Hours (Figures in Billion USD)";
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
        val = re.sub('[^0-9\.\-]', '', val)
        datetimeentry = valdict['entrydatetime'] # Need to ensure datetime are sorted
        datetimeentry = re.sub('\:\d+\.\d+$', '', datetimeentry)
        if currency_vals.has_key(currname):
            data = list([])
            data = currency_vals[currname]
            #print "CURRNAME: ", currname,"\n"
            data.append(val)
            #print "DATA: ", data, "\n"
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
    ifacedict['plotname'] = "Total Volume (Percentage)";
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
    df = pd.DataFrame(list(data))
    tp_open_index = 0
    by_currency_name = df.groupby('currency_name')
    time_series = []
    volume_traded = []
    currency_names = []
    #register_matplotlib_converters()
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
                #print "\n******************* ", ts_open, " ### ", list(currency_grp[1]['volume_traded'])[ctr], " **********************\n"
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
    datarecs = []
    currencynames = []
    datelists = []
    datadict = {}
    paramsdict = {}
    ifacedict = {}





    # Now start the plotting for plots!
    """
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
    """

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


@ensure_csrf_cookie
@csrf_protect
def coinbaseindexdisplay(request):
    if request.METHOD != "POST":
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    return HttpResponse("<img src='https://index-am.coinbase.com/oembed.json?url=https://index-am.coinbase.com/widget/index&maxwidth=500&maxheight=200'>")



