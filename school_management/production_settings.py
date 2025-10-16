"""
Production settings for School Management System
"""
from .settings import *
import os

# Production mode
DEBUG = False
ALLOWED_HOSTS = ['*']  # Configure with your domain

# Security settings (HTTP compatible)
SECURE_SSL_REDIRECT = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session security (HTTP compatible)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Static files optimization
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 year cache

# Template caching
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Database optimization
DATABASES['default']['CONN_MAX_AGE'] = 60

# Logging for production
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'

# Cache optimization
CACHES['default']['TIMEOUT'] = 3600  # 1 hour
CACHES['default']['OPTIONS']['MAX_ENTRIES'] = 10000

print("Production mode enabled with optimized settings")