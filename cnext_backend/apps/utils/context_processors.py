# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings


def common(request):

	return {
		'debug': settings.DEBUG,
		'MEDIA_URL': settings.MEDIA_URL,
	}