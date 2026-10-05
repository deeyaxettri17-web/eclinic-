"""Django settings for the E-Clinic project."""

import os
import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


# Vercel sets VERCEL=1 in its build and runtime environments.
ON_VERCEL = bool(os.environ.get('VERCEL'))

# Debug is on locally and off on Vercel unless DJANGO_DEBUG says otherwise.
DEBUG = os.environ.get('DJANGO_DEBUG', '0' if ON_VERCEL else '1') == '1'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        # Sessions are signed with this key, so a guessable default would let
        # anyone forge a login.
        raise ImproperlyConfigured('Set the DJANGO_SECRET_KEY environment variable.')
    SECRET_KEY = 'django-insecure-dev-only-change-me-in-production'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = [
    origin for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin
]
if ON_VERCEL:
    ALLOWED_HOSTS.append('.vercel.app')
    CSRF_TRUSTED_ORIGINS.append('https://*.vercel.app')

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'clinic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eclinic.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eclinic.wsgi.application'


# Database
# A local SQLite file. On Vercel only the temp dir is writable, and the file is
# rebuilt from code on every cold start (see eclinic/wsgi.py), so data entered
# on the live site is temporary.
RUNTIME_DIR = Path(tempfile.gettempdir()) / 'eclinic' if ON_VERCEL else BASE_DIR
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': RUNTIME_DIR / 'db.sqlite3',
    }
}

# Each Vercel instance has its own database file, so keep logins in signed
# cookies rather than the database; they then work on whichever instance
# serves the next request.
if ON_VERCEL:
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'


# Authentication
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Language and time
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True


# Static and uploaded files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    # Vercel has no collectstatic step, so serve plain files straight from the
    # app/static folders instead of the hashed copies collectstatic produces.
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
WHITENOISE_USE_FINDERS = True

MEDIA_URL = 'media/'
MEDIA_ROOT = RUNTIME_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
