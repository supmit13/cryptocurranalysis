# Django specific imports...
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect, QueryDict
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
#from django.utils import simplejson # Since django no longer ships simplejson as a part of it.
import simplejson
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.utils.translation import ugettext as _
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.template import Template, Context
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.backends.db import SessionStore
from django.middleware.csrf import get_token
from passlib.hash import pbkdf2_sha256 # To create hash of passwords
# We will use that as our sessionid.

# Standard libraries...
import os, sys, re, time, datetime
import cPickle, urlparse
import decimal, math, base64

# Application specific libraries...
from cryptocurry.analysis.views import datasourceentryiface
import cryptocurry.errors as err
import cryptocurry.utils as utils
from cryptocurry.crypto_settings import * 




def make_password(password):
    hash = pbkdf2_sha256.encrypt(password, rounds=200, salt_size=16)
    return hash


def authenticate(uname, passwd):
    db = utils.get_mongo_client()
    try:
        rec = db["users"].find({'username' : uname})
        if not rec:
            return None
        passwd_hashed = make_password(passwd)
        r = rec.next()
        password = r["password"]
        if passwd_hashed == password:
            return uname
        else:
            return None
    except:
        return None
    

def generatesessionid(username, csrftoken, userip, ts):
    hashstr = make_password(username + csrftoken + userip) + ts
    return hashstr


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    username = request.POST.get('username') or ""
    password = request.POST.get('password') or ""
    keeploggedin = request.POST.get('keepmesignedin') or 0
    csrfmiddlewaretoken = request.POST.get('csrfmiddlewaretoken', "")
    db = utils.get_mongo_client()
    uname = authenticate(username, password)
    if not uname: # Incorrect password - return user to login screen with an appropriate message.
        message = error_msg('1002')
        return HttpResponseRedirect(utils.gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
    else: # user will be logged in after checking the 'active' field
        rec = db["users"].find({"username" : uname})
        if not rec:
            message = error_msg('1002')
            return HttpResponseRedirect(utils.gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
        r = rec.next()
        active = r["active"]
        if active == "true":
            sessionid = ""
            clientip = utils.get_client_ip(request)
            timestamp = int(time.time())
            sessionid = generatesessionid(username, csrfmiddlewaretoken, clientip, timestamp.__str__())
            sessionuserrec = db["users"].find({'username' : username})
            sessuserrec = sessionuserrec.next()
            sessionuser = sessuserrec["userid"]
            sessendtime = ''
            timestamp = time.time()
            useragent = request.META['HTTP_USER_AGENT']
            insertd = {'sessionid' : sessionid, 'userid' : sessionuser, 'sessionstarttime' : timestamp, 'sessionendtime' : sessendtime, 'sourceip' : clientip, 'useragent' : useragent, 'sessionactive' : True}
            db.sessions.insert(insertd)
            response = HttpResponseRedirect(utils.gethosturl(request) + "/" + LOGIN_REDIRECT_URL)
            response.set_cookie('sessioncode', sessionid)
            response.set_cookie('userid', sessionuser)
            return response
        else:
            message = error_msg('1003')
            return HttpResponseRedirect(utils.gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)


def display_login_screen(request):
    message = ''
    if request.method != 'GET': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    cxtdict = {}
    cxtdict['urlprefix'] = utils.gethosturl(request)
    csrf_token = get_token(request)
    cxtdict.update(csrf(request))
    cxt = RequestContext(request, cxtdict)
    rtr = render_to_response("loginform.html", cxtdict, context_instance=cxt)
    return HttpResponse(rtr)





