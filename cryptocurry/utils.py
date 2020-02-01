import os, sys, time, re
import pymongo
import pandas as pd
import random
import uuid, glob
from passlib.hash import pbkdf2_sha256 # To create hash of passwords
import matplotlib.pyplot as plt
import random
import simplejson as json
from datetime import datetime
import urllib, urllib2
from PIL import Image

from cryptocurry.crypto_settings import *
import settings
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

from django.core.mail import send_mail
try:
    from json.decoder import JSONDecodeError as JSONError
except ImportError:
    JSONError = ValueError


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
AVAILABILITY_URL = "auth/username/availability/"

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
            if rec and rec[0]['sessionactive'] == 1: # user is logged in
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
                        keeploggedin = r['keeploggedin']
                        #r.update({'sessionid' : sesscode}, {'userid' : user_id, 'sessionstarttime' : t, 'sessionendtime' : str(tnow), 'sessionactive' : 0, 'sessionid' : sesscode, 'useragent' : ua, 'clientip' : clientip})
                        break
                    if not keeploggedin:
                        destroy_conn(db)
                        if DEBUG:
                            print("... but the session has expired. Needs to login again.\n")
                        return False # surpassed the maximum time for which the session was valid
                return True
            else:
                if DEBUG:
                    print("User is not logged in. Needs to login.\n")
                for r in rec:
                    t = float(r['sessionstarttime'])
                    sesscode = r['sessionid']
                    user_id = r['userid']
                    tnow = datetime.now()
                    dtimestr = tnow.strftime("%Y-%m-%d %H:%M:%S")
                    active = 0
                    clientip = r['clientip']
                    keeploggedin = r['keeploggedin']
                    #r.update_one({'sessionid' : sesscode}, {"$set" : {'userid' : user_id, 'sessionstarttime' : t, 'sessionendtime' : dtimestr, 'sessionactive' : active, 'sessionid' : sesscode, 'useragent' : ua, 'clientip' : clientip}})
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
                response = HttpResponseRedirect(gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
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


def sendemail(emailid, subject, message, fromaddr):
    """
    Method to send an email to the email id of the user passed in as the argument.
    Should be done asynchronously - put the email in a queue from where the email
    handler will pick in batches of (say) 10 emails at a time and send them before
    running to pick up the next batch.
    """
    retval = 0
    try:
        retval = send_mail(subject, message, fromaddr, [emailid,], False)
        return retval
    except:
        if mysettings.DEBUG:
            print "sendemail failed for %s - %s\n"%(emailid, sys.exc_info()[1].__str__())
        return None


def getusernamefromuserid(userid):
    db = get_mongo_client()
    usrrec = db.users.find({'userid' : userid})
    username = ""
    if usrrec:
        try:
            username = usrrec[0]['username']
        except:
            username = ""
    return username



def mkdir_p(path):
    if not os.access(path, os.F_OK):
        os.makedirs(path)
        os.chmod(path, 0666)


def get_extension(tmpfilepath):
    """
    Get the extension of a temporary file created using tempfile.mkstemp
    """
    fileparts = tmpfilepath.split(".")
    if fileparts.__len__() < 2:
        return ""
    ext = fileparts[1][0:3]
    return ext


def get_extension2(filename):
    """
    Replica of 'get_extension' defined in earlier. In previous version,
    the file extension is assumed to be 3 chars long only. Hence, in this present
    scenario, it doesn't work. This version handles that scenario.
    """
    extPattern = re.compile("\.(\w{3,4})$")
    extMatch = extPattern.search(filename)
    ext = ""
    if extMatch:
        ext = extMatch.groups()[0]
    return ext


def checkimagewithpil(path):
    try:
        Image.open(path)
    except IOError:
        return False
    return True


def handleuploadedfile2(uploaded_file, targetdir, filename=settings.PROFILE_PHOTO_NAME):
    """
    Replica of 'handleuploadedfile' defined in earlier. In previous version,
    the file extension is assumed to be 3 chars long only. Hence, in this present
    scenario, it doesn't work. This version handles that scenario.
    """
    mkdir_p(targetdir)
    if uploaded_file.size > MAX_FILE_SIZE_ALLOWED:
        message = err.error_msg['1005']
        return [ None, message, '' ]
    ext = get_extension2(uploaded_file.name)
    destinationfile = os.path.sep.join([ targetdir, filename + "." + ext, ])
    # Check if destination file is an image file
    #tf = checkimagewithpil(destinationfile)
    #if not tf:
    #    return [] # Not an image file, so we return an empty list
    with open(destinationfile, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
        destination.close()
        os.chmod(targetdir, 0777)
        os.chmod(destinationfile, 0777) # Is there a way to club these 'chmod' statements?
    if DEBUG:
        print(filename + "." + ext + " in utils.handleuploadedfile2\n\n")
    return [ destinationfile, '', filename + "." + ext ]


def getprofileimgtag(request):
    """
    Function to form the img tag for profile image based on whether
    the user has a profile image or not.
    """
    db = get_mongo_client()
    if request.COOKIES.has_key('sessioncode'):
        sesscode = request.COOKIES['sessioncode']
    else:
        sesscode = ""
    if request.COOKIES.has_key('userid'):
        userid = request.COOKIES['userid']
    else:
        userid = ""
    if request.POST.has_key('userid'):
        userid = request.POST['userid']
    userrec = db.users.find({'userid': userid})
    if not userrec or userrec.count() < 1:
        return ""
    username = userrec[0]['username']
    profimgfile = userrec[0]['userimagepath'] # Actually, this is the filename
    csrftoken = ''
    if request.COOKIES.has_key('csrftoken'):
        csrftoken = request.COOKIES['csrftoken']
    profimagepath = os.path.sep.join([ settings.MEDIA_ROOT, username, "images", profimgfile ])
    profileimgtag = "<img src='media/square.png' height='50' width='50' alt='Profile Image' id='profileimage'><div id='uploadbox' style='display: none;'></div><a href='#' onClick='return uploader(&quot;%s&quot;,&quot;%s&quot;);'><font size='-1'>upload profile image</font></a>"%(settings.PROFIMG_CHANGE_URL, csrftoken)
    if DEBUG:
        print(profimagepath + "\n----------------\n" + profimgfile + "\n\n")
    if os.path.exists(profimagepath) and profimgfile != "":
        profileimgtag = "<img src='media/%s/images/%s' height='90' width='90' alt='Profile Image'><div id='uploadbox' style='display: none;'></div><a href='#' onClick='return uploader(&quot;%s&quot;, &quot;%s&quot;);'><font size='-1'>change profile image</font></a>"%(username, profimgfile, settings.PROFIMG_CHANGE_URL, csrftoken)
    return profileimgtag


def populate_ifacedict_basic(request):
    curdate = datetime.now()
    prof_img_tag = getprofileimgtag(request)
    (username, password, password2, email, firstname, middlename, lastname, mobilenum) = ("", "", "", "", "", "", "", "")
    c = {'curdate' : curdate, 'login_url' : gethosturl(request) + "/" + LOGIN_URL, 'hosturl' : gethosturl(request),\
             'register_url' : gethosturl(request) + "/" + REGISTER_URL,\
             'min_passwd_strength' : MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
             'hosturl' : gethosturl(request), 'profpicheight' : PROFILE_PHOTO_HEIGHT, 'profpicwidth' : PROFILE_PHOTO_WIDTH, 'availabilityURL' : AVAILABILITY_URL, 'register_url' : REGISTER_URL, 'profile_image_tag' :  prof_img_tag}
    return c


def check_password_strength(passwd):
    if passwd.__len__() == 0:
        return 0
    strength = 0
    if passwd.__len__() > 6:
        strength += 1
    contains_digits, contains_special_char, contains_lowercase, contains_uppercase = 0, 0, 0, 0
    special_characters = "~`!#$%^&*+=-[]\\\';,/{}|\":<>?"
    i = 0
    while i < passwd.__len__() - 1:
        if passwd[i] >= '0' and passwd[i] <= '9':
            strength += 1
            i += 1
            continue
        if passwd[i] == passwd[i].upper():
            strength += 1
            i += 1
            continue
        if passwd[i] == passwd[i].lower():
            strength += 1
            i += 1
            continue
        if passwd[i] in special_characters:
            strength += 1
            i += 1
            continue
        i += 1
    return strength


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

"""
Function to validate a wallet's name.
"""
def validate_wallet_name(walletname):
    """
    For now, the basic rule is to create a name that is at least 10
    characters long and starts with an alphabet. The name will be 
    case-sensitive, and may contain both alphabets as well as numeric
    values.
    """
    name_pattern = re.compile("^([a-zA-Z])([\w\d]{9,})")
    if re.search(name_pattern, walletname):
        return True
    else:
        if DEBUG:
            print "Walletname: %s\n"%walletname
        return False

"""
Rules for creating a valid wallet name
"""
def rules_valid_name():
    rules = "1. Name should start with an alphabet (either lowercse or uppercase).<br />2. Names can contain both alphabets and numbers.<br />3. Names should be at least 10 characters long.<br />4. Wallet names may not have whitespace characters."
    return rules

def isStringEmpty(string):
    string = string.strip()
    if not string or string == "":
        return True
    return False


def check_wallet_limits(userid):
    db = get_mongo_client()
    usertype = 'GENERAL'
    rec = db.users.find({'userid' : userid})
    try:
        if rec.count() > 0:
            usercode = rec['usertype']
            if usercode == '0':
                usertype = 'GENERAL'
            elif usercode == '1':
                usertype = 'SILVER'
            elif usercode == '2':
                usertype = 'GOLD'
            elif usercode == '3':
                usertype = 'PLATINUM'
        else:
            pass
    except:
        pass
    rec_total = db.wallets.find({'userid' : userid})
    max_limit = NUM_WALLETS_GENERAL
    if usertype == 'SILVER':
        max_limit = NUM_WALLETS_SILVER
    elif usertype == 'GOLD':
        max_limit = NUM_WALLETS_GOLD
    elif usertype == 'PLATINUM':
        max_limit = NUM_WALLETS_PLATINUM
    else:
        pass
    if rec_total.count() >= max_limit:
        return False
    else:
        return True


def check_currency_limits(userid, currencyname):
    db = get_mongo_client()
    usertype = 'GENERAL'
    rec = db.users.find({'userid' : userid})
    try:
        if rec.count() > 0:
            usercode = rec['usertype']
            if usercode == '0':
                usertype = 'GENERAL'
            elif usercode == '1':
                usertype = 'SILVER'
            elif usercode == '2':
                usertype = 'GOLD'
            elif usercode == '3':
                usertype = 'PLATINUM'
        else:
            pass
    except:
        pass
    rec_total = db.wallets.find({'userid' : userid, 'currencyname' : currencyname.lower()})
    max_limit = NUM_WALLETS_PER_CURRENCY_GENERAL
    if usertype == 'SILVER':
        max_limit = NUM_WALLETS_PER_CURRENCY_SILVER
    elif usertype == 'GOLD':
        max_limit = NUM_WALLETS_PER_CURRENCY_GOLD
    elif usertype == 'PLATINUM':
        max_limit = NUM_WALLETS_PER_CURRENCY_PLATINUM
    else:
        pass
    if rec_total.count() >= max_limit:
        return False
    else:
        return True


currmap = {'Binance Coin' : 'bnb', 'Bitcoin' : 'btc',  'EOS' : 'eos', 'Litecoin' : 'ltc', 'Ripple' : 'xrp', 'Ethereum' : 'eth', 'Bitcoin Cash' : 'bch', 'Ethereum Classic' : 'etc', 'Monero' : 'xmr', 'Stellar' : 'xlm', 'Bitcoin Gold' : 'btg', 'NEO' : 'neo' }


def get_valid_json(request, allow_204=False):
    if request.status_code == 429:
        raise RateLimitError('Status Code 429', request.text)
    elif request.status_code == 204 and allow_204:
        return True
    try:
        return request.json()
    except JSONError as error:
        msg = 'JSON deserialization failed: {}'.format(str(error))
        raise requests.exceptions.ContentDecodingError(msg)


def validate_args(varvalue, vartype):
    varvalue = str(varvalue)
    walletnamepattern = re.compile(r"^[a-zA-Z][\w\d]+$") # Should contain only alphanumeric characters and start with an alphabet.
    walletaddresspattern = re.compile(r"^[\w\d]+$") # Should contain only alphabets and numeric digits.
    banknamepattern = re.compile(r"^[a-zA-Z][\w\s\&]*$") # Should start with alphabets and contain alphanumeric characters, '&' and spaces.
    accountnumberpattern = re.compile(r"^[\d]+$") # Should contain numeric digits only.
    accountnamepattern = re.compile(r"^[a-zA-Z][a-zA-Z\s]*$") # Should contain only alphabets and space characters.
    bankcodepattern = re.compile(r"^[\w\d]+$") # Should contain only alphanumeric characters.
    if vartype == 'wallet_name':
        m = walletnamepattern.match(varvalue)
        if not m:
            message = "msg:err:Wallet name is not in correct format. Wallet name may contain alphanumeric characters and should start with a alphabet."
            return message
    elif vartype == 'wallet_address':
        m = walletaddresspattern.match(varvalue)
        if not m:
            message = "msg:err:Wallet Address is not in correct format. Wallet address may contain alphanumeric characters only."
            return message
    elif vartype == 'bank_name':
        m = banknamepattern.match(varvalue)
        if not m:
            message = "msg:err:Bank name is not in correct format. Bank name may contain alphabets, & and spaces, and should start with an alphabet."
            return message
    elif vartype == 'account_number':
        m = accountnumberpattern.match(varvalue)
        if not m:
            message = "msg:err:Account number is not in correct format. Account number may contain numeric digits only."
            return message
    elif vartype == 'account_name':
        m = accountnamepattern.match(varvalue)
        if not m:
            message = "msg:err:Account name is not in correct format. Account name may contain alphabets and spaces only."
            return message
    elif vartype == 'bank_code':
        m = bankcodepattern.match(varvalue)
        if not m:
            message = "msg:err:Bank code is not in correct format. Bank code may contain alphanumeric characters and should start with a alphabet."
            return message
    return ""


def checkaccountbalance(bankname, bankcode, accountnumber, accountname):
    return 0.00




