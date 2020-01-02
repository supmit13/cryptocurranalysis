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
    #for currencyname in datadict.keys():
    #    print "\n\n\n", currencyname, " === ", datadict[currencyname], " \nddd###################################\n "
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
        #print currname, "\n"
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
        #print currname, " ", val, "\n***********************************99\n\n"
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
        #print currname, "\n"
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
        #print currname, "\n"
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
        #print currname, "\n"
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
        #print currname, "\n"
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
        #print currname, "\n"
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
    #print (str(ifacedict) + "\n##################################\n")
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
        #print currname, "\n"
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
        #print currname, "\n"
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
    return HttpResponse("You are logged in successfully as '%s'!"%username)


@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def profileimagechange(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    userid = request.COOKIES['userid']
    db = utils.get_mongo_client()
    rec = db["users"].find({'userid' : userid})
    if rec and rec.count() > 0:
        username = rec[0]['username']
    else:
        message = "failed - Anonymous users can't upload profile pics."
        return HttpResponse(message)
    message = ""
    if request.FILES.has_key('profpic'):
        fpath, message, profpic = utils.handleuploadedfile2(request.FILES['profpic'], MEDIA_ROOT + os.path.sep + username + os.path.sep + "images")
        tbl = db["users"]
        tbl.update_one({'userid' : userid, 'sessionid' : sesscode}, {"$set":{'userimagepath' : profpic},  "$currentDate":{"lastModified":True}})
        message = "success"
    else:
        message = "failed"
    return HttpResponse(message)


# ======================== Blockcypher API calls ============================= #
@utils.is_session_valid
@utils.session_location_match
@csrf_protect
def get_blockcypher_private_public_keys_address():
    api_endpoint = BLOCKCYPHER_ADDRESS_ENDPOINT
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), utils.NoRedirectHandler())
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : BLOCKCYPHER_HOST }
    blockcypher_request = urllib2.Request(api_endpoint, None, http_headers)
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
    if request.POST.has_key(address) and request.POST["address"] != "":
        address = request.POST["address"]
    if blockcypher_data.has_key('wif'):
        wif = blockcypher_data['wif'] # Wallet Import Format - a common encoding for the private key
    if not private or not public or not address or not wif:
        message = "msg:err:Could not retrieve all the data to create a wallet. Please try again after some time." # TODO: Need to tell user what to do if it keeps failing
        response = HttpResponse(message)
        return response 
    # Create the wallet for the user and put it in the DB in the 'wallets' collection.
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : BLOCKCYPHER_HOST }
    postdata = {'name' : walletname, 'addresses' : [address, ], 'token' : BLOCKCYPHER_ACCOUNT_TOKEN}
    encoded_data = urllib.urlencode(postdata)
    api_endpoint = "https://api.blockcypher.com/v1/btc/main/wallets"
    blockcypher_request = urllib2.Request(api_endpoint, encoded_data, http_headers)
    blockcypher_response = None
    try:
        blockcypher_response = opener.open(blockcypher_request)
    except:
        print "msg:err:Could not get the blockcypher wallet data - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    if not blockcypher_response:
        print "msg:err:Could not retrieve response from the request to '%s'\n"%api_endpoint
        return False
    blockcypher_data_json = blockcypher_response.read()
    if DEBUG:
        print(blockcypher_data_json)
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
    message = "Your wallet was created successfully. Please make a note of the following:\nPublic Key: %s\nPrivate Key: %s\nAddress: %s\nWallet Name: %s"%(public, private, address, walletname)
    message += "<br />Please also note that we are NOT going to store the private key in our database. It is your responsibility to store it at a safe location. You will need it during transactions and trading, and during those operations you would be asked to provide your private key so that we may process your requests.<br />If you lose your private key, you basically lose your wallet.<br />Please also make a note of all the parameters shown above."
    response = HttpResponse(message)
    return response


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
    walletname, addresses = "", ""
    if request.POST.has_key('walletname'):
        walletname = request.POST['walletname']
        if utils.isStringEmpty(walletname):
            message = "The required parameter 'walletname' cannot be empty. Please specify the wallet name at the appropriate field on the form and try again."
            response = HttpResponse(message)
            return response
        walletname = walletname.strip()
    else:
        message = "The required parameter 'walletname' couldn't be found. Please specify the wallet name at the appropriate field on the form and try again."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('addresses'):
        addresses = request.POST['addresses']
        addresses = addresses.strip()
        if utils.isStringEmpty(addresses) or addresses.find(",") == -1:
            message = "The required parameter 'addresses' cannot be empty. Please specify the addresses you want to add to the wallet at the appropriate field on the form and try again."
            response = HttpResponse(message)
            return response
    else:
        message = "The required parameter 'addresses' couldn't be found. Please specify the addresses you want to add to your wallet at the appropriate field on the form and try again."
        response = HttpResponse(message)
        return response
    addresses_list = addresses.split(",")
    # Now check if the wallet exist in our DB and it is owned by the user specified using the username.
    db = utils.get_mongo_client()
    rec = db.wallets.find({'username' : username, 'wallet_name' : walletname})
    currencyname, balance_amt, public_key, wif, dtimestr = "", "", "", "",""
    if not rec or rec.count < 1:
        message = "It seems that you have specified a wrong wallet name. Either the wallet doesn't exist or you are not the owner of the wallet. Kindly rectify your mistake and try again."
        response = HtpResponse(message)
        return response
    else:
        currencyname = rec[0]['currencyname']
        balance_amt = rec[0]['balance_amt']
        public_key = rec[0]['public_key']
        wif = rec[0]['wif']
        timenow = datetime.datetime.now()
        dtimestr = timenow.strftime("%Y-%m-%d %H:%M:%S")
    # If we reach here, it means that the named wallet is owned by the user requesting to add the address.
    # Let's oblige her/him. For every address, a new document will be added to the 'wallets' collection.
    for addr in addresses_list:
        qset = {'userid' : userid, 'username' : username, 'currencyname' : currencyname.lower(), 'balance_amt' : balance_amt, 'last_updation' : dtimestr, 'wallet_address' : addr, 'public_key' : public_key, 'wif' : wif, 'wallet_name' : walletname}
        try:
            db.wallets.insert_one(qset)
        except:
            message = "Couldn't add the address to the wallet - Error: %s\n"%sys.exc_info()[1].__str__()
            response = HttpResponse(response)
            return response
    # Now, send a request with the necessary params to the API hook to keep blockcypher in sync.
    api_endpoint = "https://api.blockcypher.com/v1/btc/main/wallets/%s/addresses?token=%s"%(walletname, BLOCKCYPHER_ACCOUNT_TOKEN)
    addresses_list_str = ",".join(addresses_list)
    postdata = {'addresses' : [addresses_list_str]}
    encoded_data = urllib.urlencode(postdata)
    http_headers = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : BLOCKCYPHER_HOST }
    blockcypher_request = urllib2.Request(api_endpoint, encoded_data, http_headers)
    blockcypher_response = None
    try:
        blockcypher_response = opener.open(blockcypher_request)
    except:
        print "Could not add the blockcypher addresses data to the wallet - Error: %s\n"%sys.exc_info()[1].__str__()
        return False
    if not blockcypher_response:
        print "Could not retrieve response from the request to '%s'\n"%api_endpoint
        return False
    blockcypher_response_json = blockcypher_response.read()
    blockcypher_response_dict = json.loads(blockcypher_response_json)
    if blockcypher_response_dict.has_key('token') and blockcypher_response_dict['token'] == BLOCKCYPHER_ACCOUNT_TOKEN and blockcypher_response_dict.has_key('name') and blockcypher_response_dict['name'] == walletname and blockcypher_response_dict.has_key('addresses'):
        message = "The address(es) have been added to the wallet successfully."
        response = HttpResponse(message)
        return response
    else:
        message = "For some reason, the address(es) could not be added to the named wallet. Please try again. If the error persists, please contact the admin with the wallet and address details at admin@cryptocurry.me"
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
    message += "<div style='color:#0000AA;'>You have the following wallets:<br />"
    for r in rec:
        walletname = r["wallet_name"]
        currency = r["currencyname"]
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








