from .base import *  # noqa: F401,F403

DEBUG = False

# Static files are collected to STATIC_ROOT and served by WhiteNoise.
# CompressedManifestStaticFilesStorage gzip/brotli-compresses them and appends
# a content hash to each name so they can be cached forever.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
