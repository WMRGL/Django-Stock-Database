
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '<insert_security_key>'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts
ALLOWED_HOSTS = ['localhost',
                 '127.0.0.1', '<insert_allowed_hosts>']


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'db_name',
        'USER': 'db_user',
        'PASSWORD': 'db_pwd',
        'HOST': 'host',
        'PORT': 'port',
    },
    'Shire_Data': {
        'ENGINE': 'mssql',
        'NAME': 'db_name',
        'USER': 'db_user',
        'PASSWORD': 'db_pwd',  # Need to set env var
        'HOST': 'host',  # IP of the dbserver
        'PORT': 'port',

    },
}