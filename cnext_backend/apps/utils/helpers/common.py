import threading

import requests
import time
import os
import base64
import logging
import collections

from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db import connections

def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict
    :param cursor:
    :return: cursor queryset to list of dict
    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
    
def get_data_from_django(query, query_kwargs):
    """
    common function to fetch data from django
    :param query:
    :return: return django data from query
    """
    
    cursor = connections['default'].cursor()
    
    cursor.execute(query, query_kwargs)
    data = dictfetchall(cursor)
    cursor.close()
    return data