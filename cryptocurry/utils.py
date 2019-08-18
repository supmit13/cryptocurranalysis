import os, sys, time, re
import pymongo
import pandas as pd
import random
import uuid, glob

from cryptocurry.crypto_settings import * 
import cryptocurry.errors as err

from django.views.decorators.csrf import csrf_exempt, csrf_protect
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


def get_mongo_client():
    client = pymongo.MongoClient(DB_HOST, DB_PORT)
    db = client[DB_NAME]
    return db


def destroy_conn(db):
    db = None

def randomcolorgenerator():
    a= random.randint(10,99)
    b = random.randint(10,99)
    c = random.randint(10, 99)
    color = "#" + str(a) + str(b) + str(c)
    return color


def isloggedin(request):
    """
    Creates and returns a session object if the request is a
    valid and authenticated session. Returns None otherwise.
    """
    if not request.COOKIES.has_key('sessioncode'):
        if DEBUG:
            print "Invalid session code.\n"
        return False
    if not request.COOKIES.has_key('userid'):
        if DEBUG:
            print "Invalid session code.\n"
        return False
    sesscode = request.COOKIES['sessioncode']
    userid = request.COOKIES['userid']
    ua = request.META['HTTP_USER_AGENT']
    db = get_mongo_client()
    rec = db['sessions'].find({'sessionid' : sesscode })
    if not rec:
        destroy_conn(db)
        return False
    else: # The session id may or may not be valid. If invalid, an exception will be thrown.
        try:
            r = rec.next()
            if l.__len__() > 0 and r['sessionactive'] == True: # user is logged in
                t = float(r['sessionstarttime'])
                tnow = time.time()
                if tnow - t > MAX_SESSION_VALID:
                    sesscode = r['sessionid']
                    user_id = r['userid']
                    clientip = r['clientip']
                    rec.update({'sessionid' : sesscode}, {'userid' : user_id, 'sessionstarttime' : t, 'sessionendtime' : str(tnow), 'active' : False, 'sessionid' : sesscode, 'useragent' : ua, 'clientip' : clientip})
                    destroy_conn(db)
                    return False # surpassed the maximum time for which the session was valid
                return True
            else:
                t = float(r['sessionstarttime'])
                sesscode = r['sessionid']
                user_id = r['userid']
                tnow = time.time()
                active = False
                clientip = r['clientip']
                rec.update({'sessionid' : sesscode}, {'userid' : user_id, 'sessionstarttime' : t, 'sessionendtime' : str(tnow), 'active' : active, 'sessionid' : sesscode, 'useragent' : ua, 'clientip' : clientip})
                destroy_conn(db)
                return False
        except:
            return False



def gethosturl(request):
    url = URL_PROTOCOL
    host = request.get_host()
    if not host:
        if request.META.has_key('HTTP_SERVER_NAME'):
            url = url + request.META['HTTP_SERVER_NAME']
        else:
            url = url + "localhost"
        if request.META.has_key('HTTP_SERVER_PORT') and request.META['HTTP_SERVER_PORT'] != '80':
            url = url + ":" + request.META['HTTP_SERVER_PORT'].__str__()
    else:
        url = url + host
    return url


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_port(request):
    client_port = request.META.get('REMOTE_PORT')
    return client_port


def destroysession(request, sessionid):
    """
    Function to destroy a session object and return a request object.
    """
    try:
        del request.COOKIES['sessioncode']
        del request.COOKIES['userid']
    except:
        pass
    db = get_mongo_client()
    rec = db['sessions'].find({'sessionid' : request.COOKIES['sessioncode'] })
    try:
        r = rec.next()
        t = float(r['sessionstarttime'])
        sesscode = r['sessionid']
        user_id = r['userid']
        tnow = time.time()
        active = False
        rec.update({'sessionid' : sesscode}, {'userid' : user_id, 'sessionstarttime' : t, 'sessionendtime' : str(tnow), 'active' : active, 'sessionid' : sesscode})
        destroy_conn(db)
    except:
        print "The given session doen't exist"
    return request


def checksession(request):
    """
    Wrapper over isloggedin to redirect the user to login page if the
    session is found to have expired or invalid for some reason.
    Use this as it is a standard way to check the session and redirect
    to the login page if session is invalid.
    """
    if not isloggedin(request):
        message = error_msg('1006')
        return HttpResponseRedirect(gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
    else: # Return the request
        return request


def is_session_valid(func):
    """
    Decorator version of checksession to check the validity of  a session. Uses the same isloggedin function above internally.
    """
    def sessioncheck(request):
        if not isloggedin(request):
            message = error_msg('1006')
            response = HttpResponseRedirect(gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
        else: # Return the request
            response = func(request)
        return response
    return sessioncheck


def session_location_match(func):
    """
    Decorator to match the session and location info stored in DB and the ones retrieved from the request
    """
    def checkconsistency(request):
        sesscode = request.COOKIES['sessioncode']
        userid = request.COOKIES['userid']
        clientIP_fromheader = request.META['REMOTE_ADDR']
        user_id = ""
        # Check to see if the values for this session stored in DB are identical to those we extracted from the headers just now.
        db = get_mongo_client()
        try:
            rec = db['sessions'].find({'sessionid' : sesscode })
            r = rec.next()
            clientip = r['clientip']
            if not rec:
                destroy_conn(db)
            else: # The session id may or may not be valid. If invalid, an exception will be thrown.
                message = error_msg('1006')
                destroy_conn(db)
        except:
            message = error_msg('1006')
            # Create response with redirect to login page and this message as GET arg. Return that response
            response = HttpResponseRedirect(gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
        if userid != user_id or clientip != clientIP_fromheader:
            message = error_msg('1007')
            # Create response with redirect to login page and this message as GET arg. Return that response
            response = HttpResponseRedirect(gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
        else:
            response = func(request)
        return response
    return checkconsistency


def generate_random_string():
    """
    Generate a random string
    """
    random = str(uuid.uuid4())
    random = random.replace("-","")
    tstr = str(int(time.time() * 1000))
    random = random + tstr
    return random


