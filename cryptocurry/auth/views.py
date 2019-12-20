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

# Application specific libraries...
from cryptocurry.analysis.views import datasourceentryiface
import cryptocurry.errors as err
import cryptocurry.utils as utils
from cryptocurry.crypto_settings import * 

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
        return HttpResponseRedirect(utils.gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
    else: # user will be logged in after checking the 'active' field
        rec = db["users"].find({"username" : uname})
        if not rec:
            message = err.error_msg('1002')
            return HttpResponseRedirect(utils.gethosturl(request) + "/" + LOGIN_URL + "?msg=" + message)
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
            insertd = {'sessionid' : sessionid, 'userid' : sessionuser, 'sessionstarttime' : timestamp, 'sessionendtime' : sessendtime, 'sourceip' : clientip, 'useragent' : useragent, 'sessionactive' : True}
            db.sessions.insert_one(insertd)
            response = HttpResponseRedirect(utils.gethosturl(request) + "/" + OPERATIONS_URL)
            response.set_cookie('sessioncode', sessionid)
            response.set_cookie('userid', sessionuser)
            return response
        else:
            message = err.error_msg('1003')
            if DEBUG:
                print(message)
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


@csrf_protect
@never_cache
def register(request):
    privs = Privilege.objects.all()
    privileges = {}
    for p in privs:
        privileges[p.privname] = p.privdesc
    if request.method == "GET": # display the registration form
        msg = ''
        if request.META.has_key('QUERY_STRING'):
            msg = request.META.get('QUERY_STRING', '')
        if msg is not None and msg != '':
            var, msg = msg.split("=")
            for hexkey in mysettings.HEXCODE_CHAR_MAP.keys():
                msg = msg.replace(hexkey, mysettings.HEXCODE_CHAR_MAP[hexkey])
            msg = "<p style=\"color:#FF0000;font-size:14;font-face:'helvetica neue';font-style:bold;\">%s</p>"%msg
        else:
            msg = ""
        curdate = datetime.datetime.now()
        (username, password, password2, email, firstname, middlename, lastname, mobilenum) = ("", "", "", "", "", "", "", "")
        tmpl = get_template("authentication/newuser.html")
        #c = {'curdate' : curdate, 'msg' : msg, 'login_url' : utils.gethosturl(request) + "/" + mysettings.LOGIN_URL, 'register_url' : utils.gethosturl(request) + "/" + mysettings.REGISTER_URL, 'privileges' : privileges, 'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, }
        c = {'curdate' : curdate, 'msg' : msg, 'login_url' : utils.gethosturl(request) + "/" + mysettings.LOGIN_URL, 'hosturl' : utils.gethosturl(request),\
             'register_url' : utils.gethosturl(request) + "/" + mysettings.REGISTER_URL,\
             'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
             'availabilityURL' :  mysettings.availabilityURL, 'hosturl' : utils.gethosturl(request), 'profpicheight' : mysettings.PROFILE_PHOTO_HEIGHT, 'profpicwidth' : mysettings.PROFILE_PHOTO_WIDTH }
        c.update(csrf(request))
        cxt = Context(c)
        registerhtml = tmpl.render(cxt)
        for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
            registerhtml = registerhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
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
        usertype = request.POST['usertype']
        mobilenum = request.POST['mobilenum']
        profpic = ""
        #userprivilege = request.POST['userprivilege']
        csrftoken = request.POST['csrfmiddlewaretoken']
        message = ""
        # Validate the collected data...
        if password != password2:
            message = error_msg('1011')
        elif mysettings.MULTIPLE_WS_PATTERN.search(username):
            message =  error_msg('1012')
        elif not mysettings.EMAIL_PATTERN.search(email):
            message =  error_msg('1013')
        elif mobilenum != "" and not mysettings.PHONENUM_PATTERN.search(mobilenum):
            message = error_msg('1014')
        elif sex not in ('m', 'f', 'u'):
            message = error_msg('1015')
        elif usertype not in ('CORP', 'CONS', 'ACAD', 'CERT'):
            message = error_msg('1016')
        elif not mysettings.REALNAME_PATTERN.search(firstname) or not mysettings.REALNAME_PATTERN.search(lastname) or not mysettings.REALNAME_PATTERN.search(middlename):
            message = error_msg('1017')
        #elif userprivilege not in privileges:
        #    message = error_msg('1018')
        elif utils.check_password_strength(password) < mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH:
            message = error_msg('1019')
        if request.FILES.has_key('profpic'):
            fpath, message, profpic = utils.handleuploadedfile(request.FILES['profpic'], mysettings.MEDIA_ROOT + os.path.sep + username + os.path.sep + "images")
            # User's images will be stored in "MEDIA_ROOT/<Username>/images/".
        if message != "" and mysettings.DEBUG:
            print message + "\n"
        if message != "":
            curdate = datetime.datetime.now()
            tmpl = get_template("auth/newuser.html")
            c = {'curdate' : curdate, 'msg' : "<font color='#FF0000'>%s</font>"%message, 'login_url' : utils.gethosturl(request) + "/" + mysettings.LOGIN_URL,\
                 'register_url' : utils.gethosturl(request) + "/" + mysettings.REGISTER_URL, \
                 'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
                 'availabilityURL' :  mysettings.availabilityURL, 'hosturl' : utils.gethosturl(request), 'profpicheight' : mysettings.PROFILE_PHOTO_HEIGHT, 'profpicwidth' : mysettings.PROFILE_PHOTO_WIDTH }
            c.update(csrf(request))
            cxt = Context(c)
            registerhtml = tmpl.render(cxt)
            for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
                registerhtml = registerhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
            return HttpResponse(registerhtml)
        else: # Create the user and redirect to the dashboard page with a status message.
            user = User()
            #usrpriv = UserPrivilege()
            user.firstname = firstname
            user.middlename = middlename
            user.lastname = lastname
            user.displayname = username
            user.emailid = email
            user.password = make_password(password) # Store password as a hash.
            user.mobileno = mobilenum
            user.sex = sex
            user.usertype = usertype
            user.istest = False
            user.active = False # Will become active when user verifies email Id.
            user.userpic = profpic
            emailvalidkey = EmailValidationKey()
            emailvalidkey.email = email
            emailvalidkey.vkey = utils.generate_random_string()
            try:
                user.save() # New user record inserted now. 'joindate' added automatically.
                emailvalidkey.save()
            except:
                message = sys.exc_info()[1].__str__()
                tmpl = get_template("auth/newuser.html")
                curdate = datetime.datetime.now()
                c = {'curdate' : curdate, 'msg' : "<font color='#FF0000'>%s</font>"%message, 'login_url' : utils.gethosturl(request) + "/" + mysettings.LOGIN_URL,\
                 'register_url' : utils.gethosturl(request) + "/" + mysettings.REGISTER_URL, \
                 'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
                'availabilityURL' :  mysettings.availabilityURL, 'hosturl' : utils.gethosturl(request), 'profpicheight' : mysettings.PROFILE_PHOTO_HEIGHT, 'profpicwidth' : mysettings.PROFILE_PHOTO_WIDTH }
                c.update(csrf(request))
                cxt = Context(c)
                reghtml = tmpl.render(cxt)
                return HttpResponse(reghtml)
            #usrpriv.user = user
            #usrpriv.privilege = userprivilege
            #usrpriv.status = True
            #usrpriv.save() # Associated user privilege saved.
            subject = """ TestYard Registration - Activate your account on TestYard by verifying your email. """
            message = """
                Dear %s,

                Thanks for creating your account on TestYard. In order to be able to login and use it, you need
                to verify this email address (which you have entered as an input during registration). You can
                do this by clicking on the hyperlink here: <a href='%s/%s?vkey=%s'>Verify My Account</a>. Once you have ver-
                ified your account, you would be able to use it.

                If you feel this email has been sent to you in error, please get back to us at the email address
                mentioned here: support@testyard.com

                Thanks and Regards,
                %s, CEO, TestYard.
                
            """%(user.displayname, utils.gethosturl(request), mysettings.ACCTACTIVATION_URL, emailvalidkey.vkey, mysettings.MAILSENDER)
            fromaddr = "register@testyard.com"
            utils.sendemail(user, subject, message, fromaddr)
            # Print a success message and ask user to validate email. The current screen is
            # only a providential state where the user appears to be logged in but has no right
            # to perform any action.
            message = "<font color='#0000FF'>Hello %s, welcome on board TestYard(&#8482;). We hope you will have a hassle-free association with us.<br /> \
            In case of any issues, please feel free to drop us (support@testyard.com) an email regarding the matter. Our 24x7 <br />\
            support center staff would only be too glad to help you out. Happy testing... </font>"%username
            tmpl = get_template("user/profile.html")
            curdate = datetime.datetime.now()
            c = {'curdate' : curdate, 'msg' : message, 'login_url' : utils.gethosturl(request) + "/" + mysettings.LOGIN_URL, 'csrftoken' : csrftoken}
            c.update(csrf(request))
            cxt = Context(c)
            profile = tmpl.render(cxt)
            for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
                profile = profile.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
            return HttpResponse(profile)
    else: # Process this as erroneous request
        message = error_msg('1004')
        if mysettings.DEBUG:
            print "Unhandled method call during registration.\n"
        return HttpResponseBadRequest(utils.gethosturl(request) + "/" + mysettings.REGISTER_URL + "?msg=%s"%message)



"""
Check if a username is available or not.
"""
def checkavailability(request):
    username = ""
    if request.GET.has_key('username'):
        username = request.GET['username']
    user = User.objects.filter(displayname=username)
    if user.__len__() > 0: # Not available
        return HttpResponse('0')
    else: # Available
        return HttpResponse('1')



"""
view to handle account activation. We would be getting a
GET query string of the form "vkey=<some-uuid-string>".
"""
def acctactivation(request):
    vkey = ""
    if request.GET.has_key('vkey'):
        vkey = request.GET['vkey']
    else:
        return HttpResponse("Invalid request")
    if vkey == "":
        return HttpResponse("Invalid request")
    allrecs = EmailValidationKey.objects.filter(vkey=vkey)
    if allrecs.__len__() == 0: # No entry found that matches the vkey.
        return HttpResponse("Invalid Request")
    # There should not be cases where we get multiple emails for same vkey.
    # If we get that, then that is a bug in the system.
    email = allrecs[0].email # We take the first value
    user = User.objects.filter(emailid=email)
    userobj = user[0]
    userobj.newuser = False # Should no longer be considered to be a new user.
    userobj.active = True # Activate account
    try:
        userobj.save() # Email is validated now.
        curdate = datetime.datetime.now()
        tmpl = get_template("authentication/activation.html")
        msg = """
        Your email address has been validated. Now you may use your TestYard.com account by logging into it.
        """
        c = {'curdate' : curdate, 'displayname' : userobj.displayname, 'msg' : msg, 'profile_image_tag' : utils.getprofileimgtag(request) }
        c.update(csrf(request))
        cxt = Context(c)
        activehtml = tmpl.render(cxt)
        return HttpResponse(activehtml)
    except:
        return HttpResponse("Email could not be validated - %s.\n"%sys.exc_info()[1].__str__())


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
    if mysettings.DEBUG:
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
        if mysettings.DEBUG:
            print "SESSION CODE = " + sesscode
        return response
    else:
        message = "Error: %s"%error_msg('1003')
        return HttpResponseRedirect(utils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)





