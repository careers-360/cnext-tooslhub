from functools import wraps
import datetime, time
import inspect
from collections import OrderedDict
from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.apps import apps

from django.utils.decorators import decorator_from_middleware_with_args
from django.middleware.cache import CacheMiddleware

def check_auth(test_func, login_url=settings.LOGIN_URL, redirect_field_name='next'):
	def _check_group(view_func):
		@wraps(view_func)
		def wrapper(request, *args, **kwargs):
			if request.user.is_authenticated:
				if test_func(request.user):
					return view_func(request, *args, **kwargs)
				else:
					return HttpResponseForbidden('You do not have the permission to access this page.')
			else:
				if login_url.startswith('/'):
					url = login_url + '?%s=%s' % (redirect_field_name, request.get_full_path())
				else:
					url = reverse(login_url) + '?%s=%s' % (redirect_field_name, request.get_full_path())
				return redirect(url)
		return wrapper
	return _check_group


def cron_task():
	def cron_task_decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			start_time = datetime.datetime.now()
			name = func.func_code.co_filename.split('/')[-1].split('.')[0]
			task = apps.get_model('utils', 'CronTask').objects.create(name=name, start_on=start_time)
			output = func(*args, **kwargs)
			end_time = datetime.datetime.now()
			task.end_on = end_time
			task.output = output
			task.save()
		return wrapper
	return cron_task_decorator


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result
    return timed


def timer(func):
	"""helper function to estimate view execution time"""
	@wraps(func)  # used for copying func metadata
	def wrapper(*args, **kwargs):
		# record start time
		start=time.time()

		# func execution
		result=func(*args, **kwargs)

		duration=(time.time() - start) * 1000
		# output execution time to console
		if settings.DEBUG:
			print(' Function {} takes {:.2f} ms'.format(
				func.__name__,
				duration
			))
		return result

	return wrapper