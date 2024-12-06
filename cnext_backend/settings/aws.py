import os


STATICFILES_LOCATION = 'static_tools'
MEDIAFILES_LOCATION = 'media_tools'

AWS_STORAGE_BUCKET_NAME = os.getenv('S3_BUCKET_NAME','staging-cnext')

AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
    'Expires': 'Thu, 31 Dec 2025 20:00:00 GMT',
    'Cache-Control': 'max-age=86400',
}

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=6912000',
}
#AWS_QUERYSTRING_AUTH = False
#AWS_S3_SECURE_URLS = True
# AWS_IS_GZIPPED = True
AWS_DEFAULT_ACL='public-read'
AWS_PRELOAD_METADATA = True

# Add missing content types to the list of types
# that should be gzipped.
GZIP_CONTENT_TYPES = (
 'text/css',
 'application/javascript',
 'application/x-javascript',
 'text/javascript'
)

AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
STATICFILES_STORAGE = 'cnext_backend.apps.utils.custom_storage.S3ManifestStorage'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'cnext_backend.apps.utils.custom_storage.MediaStorage'

