import os, sys, time, re
import pymongo
import pandas as pd
import random

from cryptocurry.crypto_settings import * 

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


