import os

DEBUG = True

SECRET_KEY = '^7jcx7^h#b@%a76lr@a2!7xj#@4@5ayuyan9c$y#(_(8l3)_%t'
UNIT_TEST_SETTINGS = True

AUTH_API_TOKEN = 'xyz'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'kagiso_auth',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'kagiso_auth.urls'

WSGI_APPLICATION = 'kagiso_auth.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'kagiso_auth',
        'USER': os.getenv('USER'),
        'PASSWORD': 'password',
        'ATOMIC_REQUESTS': True,
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}


# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

APP_NAME = 'Test App'
AUTH_USER_MODEL = 'kagiso_auth.KagisoUser'
AUTH_FROM_EMAIL = 'noreply@kagiso.io'
SIGN_UP_EMAIL_TEMPLATE = 'xyz'
PASSWORD_RESET_EMAIL_TEMPLATE = 'xyz'

# Authomatic is mocked out in the tests, but a key lookup is still
# performed to get settings, so pass a stub back
AUTHOMATIC_CONFIG = {'jacaranda': 'zyx'}
