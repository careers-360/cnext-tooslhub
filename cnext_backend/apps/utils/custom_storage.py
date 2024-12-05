from django.conf import settings
from django.contrib.staticfiles.storage import ManifestFilesMixin
from storages.backends.s3boto3 import S3Boto3Storage
import os

class StaticStorage(S3Boto3Storage):
	location = settings.STATICFILES_LOCATION

class MediaStorage(S3Boto3Storage):
	location = settings.MEDIAFILES_LOCATION

	def __init__(self, *args, **kwargs):
		kwargs['custom_domain'] = settings.AWS_S3_CUSTOM_DOMAIN
		super(MediaStorage, self).__init__(*args, **kwargs)

class S3ManifestStorage(ManifestFilesMixin, StaticStorage):
	def __init__(self, *args, **kwargs):
		kwargs['custom_domain'] = settings.AWS_S3_CUSTOM_DOMAIN
		super(S3ManifestStorage, self).__init__(*args, **kwargs)