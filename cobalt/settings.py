import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ci8v_@0l*@1@*ufho0kt4+wu6d7b(r!0-4k9p2c^a!rki%23dr'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['test.abftech.com.au', 'uat.abftech.com.au', '127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'calendar_app.apps.CalendarAppConfig',
    'notifications.apps.NotificationsConfig',
    'events.apps.EventsConfig',
    'forums.apps.ForumsConfig',
    'masterpoints.apps.MasterpointsConfig',
    'payments.apps.PaymentsConfig',
    'support.apps.SupportConfig',
    'accounts.apps.AccountsConfig',
    'dashboard.apps.DashboardConfig',
    'user_profile.apps.UserProfileConfig',
    'results.apps.ResultsConfig',
    'logs.apps.LogsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_summernote',
    'crispy_forms',
    # 'health_check',
    # 'health_check.db',
    # 'health_check.cache',
    # 'health_check.storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cobalt.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['cobalt/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cobalt.context_processors.global_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'cobalt.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
}

if 'RDS_HOSTNAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }

AUTH_USER_MODEL="accounts.User"
AUTHENTICATION_BACKENDS = ['accounts.backend.CobaltBackend']

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.ipage.com'
EMAIL_HOST_USER = 'test@drunkguthrie.com'
EMAIL_HOST_PASSWORD = 'F1shcake'
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = 'donotreply@drunkguthrie.com'
SUPPORT_EMAIL=['m@rkguthrie.com']

if 'EMAIL_HOST' in os.environ:
    EMAIL_HOST = os.environ['EMAIL_HOST']
    EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
    DEFAULT_FROM_EMAIL = os.environ['DEFAULT_FROM_EMAIL']

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-au'
TIME_ZONE = 'Australia/Sydney'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# app specific static lives in app_name/static/app_name
# general static lives in STATICFILES_DIRS
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'cobalt/static/')]

# This is where collectstatic will put the static files it finds
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# External reference point to find static
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'

LOGIN_REDIRECT_URL="/dashboard"
LOGOUT_REDIRECT_URL="/accounts/login"

# Local settings for this Application
GLOBAL_ORG="ABF"
GLOBAL_TITLE="ABF Technology"
GLOBAL_CONTACT="https://abf.com.au"
GLOBAL_ABOUT="https://abf.com.au"
GLOBAL_PRIVACY="https://abf.com.au"
GLOBAL_PRODUCTION="abftech.com.au"
GLOBAL_MPSERVER="http://127.0.0.1:8081"

if 'GLOBAL_MPSERVER' in os.environ:
    GLOBAL_MPSERVER = os.environ['GLOBAL_MPSERVER']

# Stripe is our payment gateway

STRIPE_SECRET_KEY="sk_test_tbD1kQf7S7aBrWdpaAkdK60e"
STRIPE_PUBLISHABLE_KEY="pk_test_vx2RPX6BXeETHa3MJycvArkx"
if 'STRIPE_SECRET_KEY' in os.environ:
    STRIPE_SECRET_KEY = os.environ['STRIPE_SECRET_KEY']
    STRIPE_PUBLISHABLE_KEY = os.environ['STRIPE_PUBLISHABLE_KEY']

# django-summernote provides the rich text entry fields

SUMMERNOTE_THEME = 'bs4'

SUMMERNOTE_CONFIG = {
    'iframe': False,
    'summernote': {
        'airMode': False,
        'width': '100%',
        'height': '600',
        'lang': None,
        'spellCheck': True,
        'toolbar': [
        ['style', ['style']],
        ['font', ['bold', 'italic', 'underline']],
        ['fontname', ['fontname']],
        ['color', ['color']],
        ['para', ['ul', 'ol', 'paragraph']],
        ['table', ['table']],
        ['insert', ['link', 'picture', 'hr']],
        ['cards', ['specialcharsspades', 'specialcharshearts', 'specialcharsdiamonds', 'specialcharsclubs', 'specialcharshand']],
        ['view', ['fullscreen', 'codeview']],
        ['help', ['help']]
      ],
    },
    'attachment_require_authentication': True,
    'disable_attachment': False,
    'attachment_absolute_uri': False,
}

try:
    from .local_settings import *
except ImportError:
    pass
