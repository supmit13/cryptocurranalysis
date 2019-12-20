import os, sys, time, re
import pymongo
import pandas as pd
import random
import uuid, glob
from passlib.hash import pbkdf2_sha256 # To create hash of passwords
import matplotlib.pyplot as plt
import random
import simplejson as json

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


hextoascii = { '%3C' : '<', '%3E' : '>', '%20' : ' ', '%22' : '"', '%5B' : '[', '%5D' : ']', '%5C' : '\\', '%3A' : ':', '%3B' : ';', '%28' : '(', '%29' : ')', '%2D' : '-', '%2B' : '+', }

hexcodecharmap = { \
        '&lt;' : '<', \
        '&gt;' : '>', \
        '&amp;': '&', \
        '&nbsp;' : ' ', \
        '&quot;' : '"', \
        '&#91;' : '[', \
        '&#93;' : ']', \
        '&#39;' : '"',\
    }

billionpattern = re.compile("B$", re.IGNORECASE)


def get_mongo_client():
    client = pymongo.MongoClient(DB_HOST, DB_PORT)
    db = client[DB_NAME]
    return db


def destroy_conn(db):
    db = None

"""
def randomcolorgenerator():
    a= random.randint(0,7)
    b = random.randint(0,7)
    c = random.randint(0, 7)
    a = '0'+str(a)
    b = '0'+str(b)
    c = '0'+str(c)
    color = "#" + a + b + c
    return color
"""

def randomcolorgenerator(num_of_colors):
    colorslist = []
    for i in range(num_of_colors):
        color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        colorslist.append(color)
    return colorslist


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
            print "Invalid user Id.\n"
        return False
    sesscode = request.COOKIES['sessioncode']
    userid = request.COOKIES['userid']
    ua = request.META['HTTP_USER_AGENT']
    db = get_mongo_client()
    if DEBUG:
        print("userid: " + userid + "\nsesscode: " + sesscode + "\n")
    rec = db['sessions'].find({'sessionid' : sesscode })
    if not rec:
        destroy_conn(db)
        if DEBUG:
            print "Couldn't find a matching session Id"
        return False
    else: # The session id may or may not be valid. If invalid, an exception will be thrown.
        try:
            if rec and rec[0]['sessionactive'] == True: # user is logged in
                if DEBUG:
                    print("user is logged in...\n")
                for r in rec:
                    t = float(r['sessionstarttime'])
                    break
                tnow = time.time()
                if tnow - t > SESSION_EXPIRY_LIMIT:
                    for r in rec:
                        sesscode = r['sessionid']
                        user_id = r['userid']
                        clientip = r['clientip']
                        r.update({'sessionid' : sesscode}, {'userid' : user_id, 'sessionstarttime' : t, 'sessionendtime' : str(tnow), 'active' : False, 'sessionid' : sesscode, 'useragent' : ua, 'clientip' : clientip})
                        break
                    destroy_conn(db)
                    if DEBUG:
                        print("... but the session has expired. Needs to login again.\n")
                    return False # surpassed the maximum time for which the session was valid
                return True
            else:
                if DEBUG:
                    print("User is not logged in. Needs to login.\n")
                t = float(r['sessionstarttime'])
                for r in rec:
                    sesscode = r['sessionid']
                    user_id = r['userid']
                    tnow = time.time()
                    active = False
                    clientip = r['clientip']
                    r.update({'sessionid' : sesscode}, {'userid' : user_id, 'sessionstarttime' : t, 'sessionendtime' : str(tnow), 'active' : active, 'sessionid' : sesscode, 'useragent' : ua, 'clientip' : clientip})
                    break
                destroy_conn(db)
                return False
        except:
            print("Exception occurred: " + sys.exc_info()[1].__str__() + "\n")
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
        message = err.error_msg('1006')
        return HttpResponseRedirect(gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
    else: # Return the request
        return request


def is_session_valid(func):
    """
    Decorator version of checksession to check the validity of  a session. Uses the same isloggedin function above internally.
    """
    def sessioncheck(request):
        if not isloggedin(request):
            message = err.error_msg('1006')
            if DEBUG:
                print(message + "\n")
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
        clientip = ""
        # Check to see if the values for this session stored in DB are identical to those we extracted from the headers just now.
        db = get_mongo_client()
        try:
            rec = db['sessions'].find({'sessionid' : sesscode })
            clientip = rec[0]['sourceip']
            user_id = rec[0]['userid']
            if not rec:
                destroy_conn(db)
            else: # The session id may or may not be valid. If invalid, an exception will be thrown.
                message = err.error_msg('1006')
                destroy_conn(db)
        except:
            message = err.error_msg('1006')
            # Create response with redirect to login page and this message as GET arg. Return that response
            response = HttpResponseRedirect(gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
        if userid != user_id or clientip != clientIP_fromheader:
            if DEBUG:
                print("userid = " + userid + "\nuser_id= " + user_id + "\nclientip = " + clientip + "\nclientIP_fromheader = " + clientIP_fromheader + "\n")
            message = err.error_msg('1007')
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


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'to_dict'):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)


def default_handler(obj):
    return obj.__str__()


def make_password(password):
    hash = pbkdf2_sha256.encrypt(password, rounds=200, salt_size=16)
    return hash


def authenticate(uname, passwd):
    db = get_mongo_client()
    try:
        rec = db["users"].find({'username' : uname})
        if not rec:
            return None
        r = rec.next()
        passwd_hashed = r["password"]
        if pbkdf2_sha256.verify(passwd, passwd_hashed):
            return uname
        else:
            return None
    except:
        return None
    

def generatesessionid(username, csrftoken, userip, ts):
    hashstr = make_password(username + csrftoken + userip) + ts
    return hashstr


def sendemail(user, subject, message, fromaddr):
    pass

