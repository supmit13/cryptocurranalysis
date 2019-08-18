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
    try:
        user = User.objects.filter(displayname=uname)
        if pbkdf2_sha256.verify(passwd, user[0].password):  # Compare the hashes of the password
            return user[0]
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
    if request.method == "GET":
        msg = None
        if request.META.has_key('QUERY_STRING'):
            msg = request.META.get('QUERY_STRING', '')
        if msg is not None and msg != '':
            msg_color = 'FF0000'
            msg = skillutils.formatmessage(msg, msg_color)
        else:
            msg = ""
        # Display login form
        curdate = datetime.datetime.now()
        tmpl = get_template("authentication/login.html")
        c = {'curdate' : curdate, 'msg' : msg, 'register_url' : skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL }
        c.update(csrf(request))
        cxt = Context(c)
        loginhtml = tmpl.render(cxt)
        for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
            loginhtml = loginhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
        return HttpResponse(loginhtml)
    elif request.method == "POST":
        username = request.POST.get('username') or ""
        password = request.POST.get('password') or ""
        keeploggedin = request.POST.get('keepmeloggedin') or 0
        csrfmiddlewaretoken = request.POST.get('csrfmiddlewaretoken', "")
        userobj = authenticate(username, password)
        if not userobj: # Incorrect password - return user to login screen with an appropriate message.
            message = error_msg('1002')
            return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
        else: # user will be logged in after checking the 'active' field
            if userobj.active:
                sessobj = Session()
                clientip = request.META['REMOTE_ADDR']
                timestamp = int(time.time())
                # timestamp will be a 10 digit string.
                sesscode = generatesessionid(username, csrfmiddlewaretoken, clientip, timestamp.__str__())
                sessobj.sessioncode = sesscode
                sessobj.user = userobj
                # sessobj.starttime should get populated on its own when we save this session object.
                sessobj.endtime = None
                sessobj.sourceip = clientip
                if userobj.istest: # This session is being performed by a test user, so this must be a test session.
                    sessobj.istest = True
                elif mysettings.TEST_RUN: # This is a test run as mysettings.TEST_RUN is set to True
                    sessobj.istest = True
                else:
                    sessobj.istest = False
                sessobj.useragent = request.META['HTTP_USER_AGENT']
                # Now save the session...
                sessobj.save()
                # ... and redirect to landing page (which happens to be the profile page).
                response = HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_REDIRECT_URL)
                response.set_cookie('sessioncode', sesscode)
                response.set_cookie('userid', userobj.usertype)
                return response
            else:
                message = error_msg('1003')
                return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
    else:
        message = error_msg('1001')
        return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)


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





