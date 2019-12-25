# Django specific imports...
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie, requires_csrf_token
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
import sha256

# Application specific libraries...
from cryptocurry.analysis.views import datasourceentryiface
import cryptocurry.errors as err
import cryptocurry.utils as utils
from cryptocurry.crypto_settings import * 
import cryptocurry.settings as settings

#******* End of imports **********#


@sensitive_post_parameters()
@ensure_csrf_cookie
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
    uname = utils.authenticate(username, password)
    if not uname: # Incorrect password - return user to login screen with an appropriate message.
        message = err.error_msg('1002')
        return HttpResponse(message)
    else: # user will be logged in after checking the 'active' field
        rec = db["users"].find({"username" : uname})
        if not rec:
            message = err.error_msg('1002')
            return HttpResponse(message)
        #r = rec.next()
        for r in rec:
            active = r["active"]
            break
        if active == "true":
            sessionid = ""
            clientip = utils.get_client_ip(request)
            timestamp = int(time.time())
            sessionid = utils.generatesessionid(username, csrfmiddlewaretoken, clientip, timestamp.__str__())
            sessionuserrec = db["users"].find({'username' : username})
            #sessuserrec = sessionuserrec.next()
            for sessuserrec in sessionuserrec:
                sessionuser = sessuserrec["userid"]
                break
            sessendtime = ''
            timestamp = time.time()
            useragent = request.META['HTTP_USER_AGENT']
            insertd = {'sessionid' : sessionid, 'userid' : sessionuser, 'sessionstarttime' : timestamp, 'sessionendtime' : sessendtime, 'sourceip' : clientip, 'useragent' : useragent, 'sessionactive' : True, 'keeploggedin' : keeploggedin}
            db.sessions.insert_one(insertd)
            response = HttpResponseRedirect(utils.gethosturl(request) + "/" + OPERATIONS_URL)
            response.set_cookie('sessioncode', sessionid)
            response.set_cookie('userid', sessionuser)
            return response
        else:
            message = err.error_msg('1003')
            if DEBUG:
                print(message)
            return HttpResponse(message)


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


@ensure_csrf_cookie
@csrf_protect
@never_cache
def logout(request):
    if request.method != 'POST': # Illegal bad request... 
        message = err.ERR_INCORRECT_HTTP_METHOD
        response = HttpResponseBadRequest(message)
        return response
    
    if request.POST.has_key('userid'):
        userid = request.POST['userid']
    else:
        response = HttpResponse("2")
        response.set_cookie('userid', "")
        return response
    if request.COOKIES.has_key('sessioncode'):
        sessionid = request.COOKIES['sessioncode']
    else:
        response = HttpResponse("2")
        response.set_cookie('userid', "")
        return response
    db = utils.get_mongo_client()
    tbl = db["sessions"]
    try:
        timenow = datetime.datetime.now()
        dtimestr = timenow.strftime("%Y-%m-%d %H:%M:%S")
        if DEBUG:
            print "UserId: " + userid + "\nSessionId: " + sessionid + "\nDatetimestring: " + dtimestr + "\n\n"
        tbl.update_one({'userid' : userid, 'sessionid' : sessionid}, {"$set":{'sessionactive' : 0, 'sessionendtime' : dtimestr, 'keeploggedin' : 0},  "$currentDate":{"lastModified":True}})
        response = HttpResponse("1")
        response.set_cookie('userid', "")
        return response
    except:
        response = HttpResponse("0")
        response.set_cookie('userid', "")
        return response


@csrf_protect
@never_cache
def register(request):
    if request.method == "GET": # display the registration form
        curdate = datetime.datetime.now()
        strcurdate = curdate.strftime("%Y-%m-%d %H:%M:%S")
        (username, password, password2, email, firstname, middlename, lastname, mobilenum) = ("", "", "", "", "", "", "", "")
        tmpl = get_template("auth/regform.html")
        
        c = {'curdate' : strcurdate, 'login_url' : utils.gethosturl(request) + "/" + LOGIN_URL, 'hosturl' : utils.gethosturl(request),\
             'register_url' : utils.gethosturl(request) + "/" + REGISTER_URL,\
             'min_passwd_strength' : MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
             'hosturl' : utils.gethosturl(request), 'profpicheight' : PROFILE_PHOTO_HEIGHT, 'profpicwidth' : PROFILE_PHOTO_WIDTH, 'availabilityURL' : utils.AVAILABILITY_URL }
        c.update(csrf(request))
        
        cxt = Context(c)
        registerhtml = tmpl.render(cxt)
        for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
            registerhtml = registerhtml.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
        return HttpResponse(registerhtml)
    elif request.method == "POST": # Process registration form data
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']
        email = request.POST['email']
        firstname = request.POST['firstname']
        middlename = request.POST['middlename']
        lastname = request.POST['lastname']
        sex = request.POST['sex']
        mobilenum = request.POST['mobilenum']
        profpic = ""
        csrftoken = request.POST['csrfmiddlewaretoken']
        message = ""
        # Validate the collected data...
        if password != password2:
            message = error_msg('1011')
        elif MULTIPLE_WS_PATTERN.search(username):
            message =  error_msg('1012')
        elif not EMAIL_PATTERN.search(email):
            message =  error_msg('1013')
        elif mobilenum != "" and not PHONENUM_PATTERN.search(mobilenum):
            message = error_msg('1014')
        elif sex not in ('m', 'f', 'u'):
            message = error_msg('1015')
        elif not REALNAME_PATTERN.search(firstname) or not REALNAME_PATTERN.search(lastname) or not REALNAME_PATTERN.search(middlename):
            message = error_msg('1017')
        #elif userprivilege not in privileges:
        #    message = error_msg('1018')
        elif utils.check_password_strength(password) < MIN_ALLOWABLE_PASSWD_STRENGTH:
            message = error_msg('1019')
        if request.FILES.has_key('profpic'):
            fpath, message, profpic = utils.handleuploadedfile2(request.FILES['profpic'], settings.MEDIA_ROOT + os.path.sep + username + os.path.sep + "images")
            # User's images will be stored in "settings.MEDIA_ROOT/<Username>/images/".
        if message != "" and DEBUG:
            print message + "\n"
        if message != "":
            curdate = datetime.datetime.now()
            strcurdate = curdate.strftime("%Y-%m-%d %H:%M:%S")
            availabilityURL = utils.AVAILABILITY_URL
            tmpl = get_template("auth/regform.html")
            c = {'curdate' : strcurdate, 'msg' : "<font color='#FF0000'>%s</font>"%message, 'login_url' : utils.gethosturl(request) + "/" + LOGIN_URL,\
                 'register_url' : utils.gethosturl(request) + "/" + REGISTER_URL, \
                 'min_passwd_strength' : MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
                 'availabilityURL' :  availabilityURL, 'hosturl' : utils.gethosturl(request), 'profpicheight' : PROFILE_PHOTO_HEIGHT, 'profpicwidth' : PROFILE_PHOTO_WIDTH }
            c.update(csrf(request))
            cxt = Context(c)
            registerhtml = tmpl.render(cxt)
            for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
                registerhtml = registerhtml.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
            return HttpResponse(registerhtml)
        else: # Create the user and redirect to the dashboard page with a status message.
            db = utils.get_mongo_client()
            rec = {}
            rec['firstname'] = firstname
            rec['middlename'] = middlename
            rec['lastname'] = lastname
            rec['username'] = username
            rec['emailid'] = email
            rec['password'] = utils.make_password(password) # Store password as a hash.
            rec['mobileno'] = mobilenum
            rec['sex'] = sex
            rec['active'] = False # Will become active when user verifies email Id.
            rec['userimagepath'] = profpic
            userid = str(sha256.sha256(str(username)).hexdigest())
            if DEBUG:
                print "type of userid is " + str(type(userid)) + "\n"
            rec['userid'] = userid
            rec["address"] = {}
            rec["address"]['country'] = ""
            rec['address']['State'] = ""
            rec['address']['block_sector'] = ""
            rec['address']['house_num'] = ""
            rec['address']['street_address'] = ""
            emailvalid = {}
            emailvalid['email'] = email
            emailvalid['vkey'] = utils.generate_random_string()
            r = db.users.find({'username' : username})
            e = db.emailvalidation.find({'email' : email})
            if r.count() > 0 or e.count() > 0:
                message = "Non unique email and/or username found."
                tmpl = get_template("auth/regerror.html")
                curdate = datetime.datetime.now()
                strcurdate = curdate.strftime("%Y-%m-%d %H:%M:%S")
                availabilityURL = utils.AVAILABILITY_URL
                c = {'curdate' : strcurdate, 'msg' : message, 'login_url' : utils.gethosturl(request) + "/" + LOGIN_URL,\
                 'register_url' : utils.gethosturl(request) + "/" + REGISTER_URL, \
                 'min_passwd_strength' : MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
                'availabilityURL' :  availabilityURL, 'hosturl' : utils.gethosturl(request), 'profpicheight' : PROFILE_PHOTO_HEIGHT, 'profpicwidth' : PROFILE_PHOTO_WIDTH }
                c.update(csrf(request))
                cxt = Context(c)
                reghtml = tmpl.render(cxt)
                return HttpResponse(reghtml)
            try:
                db.users.insert_one(rec)
                db.emailvalidation.insert_one(emailvalid)
            except:
                message = sys.exc_info()[1].__str__()
                tmpl = get_template("auth/regform.html")
                availabilityURL = utils.AVAILABILITY_URL
                curdate = datetime.datetime.now()
                strcurdate = curdate.strftime("%Y-%m-%d %H:%M:%S")
                c = {'curdate' : strcurdate, 'msg' : "<font color='#FF0000'>%s</font>"%message, 'login_url' : utils.gethosturl(request) + "/" + LOGIN_URL,\
                 'register_url' : utils.gethosturl(request) + "/" + REGISTER_URL, \
                 'min_passwd_strength' : MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
                'availabilityURL' :  availabilityURL, 'hosturl' : utils.gethosturl(request), 'profpicheight' : PROFILE_PHOTO_HEIGHT, 'profpicwidth' : PROFILE_PHOTO_WIDTH }
                c.update(csrf(request))
                cxt = Context(c)
                reghtml = tmpl.render(cxt)
                return HttpResponse(reghtml)
            
            subject = """ CryptoCurry Registration - Activate your account on CryptoCurry by verifying your email. """
            message = """
                Dear %s,

                Thanks for creating your account on CryptoCurry. In order to be able to login and use it, you need
                to verify this email address (which you have entered as an input during registration). You can
                do this by clicking on the hyperlink here: <a href='%s/%s?vkey=%s'>Verify My Account</a>. Once you have ver-
                ified your account, you would be able to use it.

                If you feel this email has been sent to you in error, please get back to us at the email address
                mentioned here: support@cryptocurry.me

                Thanks and Regards,
                %s, CEO, CryptoCurry.
                
            """%(username, utils.gethosturl(request), ACCTACTIVATION_URL, emailvalid['vkey'], MAILSENDER)
            fromaddr = "register@cryptocurry.me"
            utils.sendemail(email, subject, message, fromaddr)
            # Print a success message and ask user to validate email. The current screen is
            # only a providential state where the user appears to be logged in but has no right
            # to perform any action.
            message = "<font color='#0000FF'>Hello %s, welcome on board CryptoCurry(&#8482;). We hope you will have a hassle-free association with us.<br /> \
            In case of any issues, please feel free to drop us (support@cryptocurry.com) an email regarding the matter. Our 24x7 <br />\
            support center staff would only be too glad to help you out. Happy transacting at cyptocurry... </font>"%username
            tmpl = get_template("auth/profile.html")
            curdate = datetime.datetime.now()
            strcurdate = curdate.strftime("%Y-%m-%d %H:%M:%S")
            c = {'curdate' : strcurdate, 'msg' : message, 'login_url' : utils.gethosturl(request) + "/" + LOGIN_URL, \
           'csrftoken' : csrftoken, 'username' : username, 'password' : password, 'password2' : password2, 'email' : email, \
           'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, 'userid' : userid, 'active' : 0 }
            c.update(csrf(request))
            cxt = Context(c)
            profile = tmpl.render(cxt)
            for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
                profile = profile.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
            return HttpResponse(profile)
    else: # Process this as erroneous request
        message = error_msg('1004')
        if DEBUG:
            print "Unhandled method call during registration.\n"
        return HttpResponseBadRequest(utils.gethosturl(request) + "/" + REGISTER_URL + "?msg=%s"%message)


def acctactivate(request):
    vkey = ""
    if request.GET.has_key('vkey'):
        vkey = request.GET['vkey']
    else:
        return HttpResponse("Invalid request")
    if vkey == "":
        return HttpResponse("Invalid request")
    tmpl = get_template("auth/activation.html")
    db = utils.get_mongo_client()
    tbl = db["emailvalidation"]
    validationrec = tbl.find({'vkey' : vkey})
    if not validationrec or validationrec.count() < 1:
        msg = "The request for account activation couldn't be entertained as there is a key mismatch. Please try once more or contact the admin at admin@cryptocurry.me."
        c = {'message' : msg}
        c.update(csrf(request))
        cxt = Context(c)
        activation = tmpl.render(cxt)
        for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
            activation = activation.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
        return HttpResponse(activation)
    emailid = validationrec[0]['email']
    usrtbl = db["users"]
    rec = usrtbl.find({'emailid' : emailid})
    if not rec or rec.count() < 1:
        msg = "Couldn't find a emaid Id that matches the code given in the link. Please contact the admin at admin@cryptocurry.me with all the details."
        c = {'message' : msg}
        c.update(csrf(request))
        cxt = Context(c)
        activation = tmpl.render(cxt)
        for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
            activation = activation.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
        return HttpResponse(activation)
    if DEBUG:
        print("emailid = " + emailid + "\n------------------------------\n")
    usrtbl.update_one({'emailid' : emailid}, {"$set" : {'active' : "true"}})
    msg = "Welcome to CryptoCurry! Your account has been activated. Now you may start using it."
    c = {'message' : msg}
    c.update(csrf(request))
    cxt = Context(c)
    activation = tmpl.render(cxt)
    for htmlkey in HTML_ENTITIES_CHAR_MAP.keys():
        activation = activation.replace(htmlkey, HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(activation)


"""
Check if a username is available or not.
"""
def checkavailability(request):
    username = ""
    if request.GET.has_key('username'):
        username = request.GET['username']
    db = utils.get_mongo_client()
    rec = db.users.find({'username' : username})
    if rec.count() > 0: # Not available
        return HttpResponse('0')
    else: # Available
        return HttpResponse('1')



# Methods for handling requests from mobile handsets and other devices that may be considered in future.
@csrf_exempt
@never_cache
def mobile_verifypassword(request):
    if request.method != "POST":
        message = "Error: %s"%error_msg('1004')
        return HttpResponse(message)
    if not request.POST.has_key('data'):
        return HttpResponse("")
    postdata = request.POST['data']
    print postdata
    keystring = "test"
    ivstring = "test"
    #decryptedPostdata = utils.des3Decrypt(postdata, keystring, ivstring)
    decodedPostdata = base64.b64decode(postdata)
    namevaluepairslist = decodedPostdata.split("&")
    argdict = {}
    for namevalue in namevaluepairslist:
        name, value = namevalue.split("=")
        argdict[name] = value
    username = ""
    if argdict.has_key('username'):
        username = argdict['username']
    else:
        return HttpResponse("")
    if argdict.has_key('password'):
        password = argdict['password']
    else:
        return HttpResponse("")
    if argdict.has_key('csrfmiddlewaretoken'):
        csrftoken = argdict['csrfmiddlewaretoken']
    else:
        return HttpResponse("")
    if DEBUG:
        print "USERNAME = " + username
        print "PASSWORD = " + password
    userobj = authenticate(username, password)
    if not userobj:
        return HttpResponse("Error: %s"%error_msg('1002'))
    if userobj.active:
        sessobj = Session()
        clientip = request.META['REMOTE_ADDR']
        timestamp = int(time.time())
        sesscode = generatesessionid(username, csrftoken, clientip, timestamp.__str__())
        sessobj.sessioncode = sesscode
        sessobj.user = userobj
        sessobj.endtime = None
        sessobj.sourceip = clientip
        sessobj.useragent = request.META['HTTP_USER_AGENT']
        sessobj.save()
        response = HttpResponse("sesscode=" + sesscode)
        response.set_cookie('sessioncode', sesscode)
        response.set_cookie('usertype', userobj.usertype)
        if DEBUG:
            print "SESSION CODE = " + sesscode
        return response
    else:
        message = "Error: %s"%error_msg('1003')
        return HttpResponseRedirect(utils.gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)





