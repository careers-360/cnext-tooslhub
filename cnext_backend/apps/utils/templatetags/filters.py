# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
	from django.contrib.staticfiles.templatetags.staticfiles import static
except ImportError:
	from django.templatetags.static import static
	
from django_jinja import library
import jinja2
import copy, os
import datetime
try:
	from urllib.parse import urlparse
except ImportError:
	from urlparse import urlparse #type:ignore
	from urlparse import parse_qs #type:ignore

from datetime import timedelta, time
from time import strftime
from time import gmtime
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.db.models import Avg
from django.db.models import Max
from django.db.models import Sum
from django.db.models import Min

from django.urls import reverse

from django.utils import timezone
from dateutil import parser
from bs4 import BeautifulSoup
import requests
from django.conf import settings
from django.utils.safestring import mark_safe
# from jinja2 import contextfunction
import math
import re

from django.core.files.storage import get_storage_class



@library.global_function
def get_days_from_end_date(date):
	return (datetime.datetime.combine(date, datetime.time())-datetime.datetime.now()).total_seconds()/86400.0