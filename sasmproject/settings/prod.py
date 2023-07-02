from .base import *
DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': env('SASM_BE_DB_ENGINE'),
        'NAME': env('SASM_BE_DB_NAME'),
        "USER": env('SASM_BE_DB_USER'),
        "PASSWORD": env('SASM_BE_DB_PASSWORD'),
        "HOST": env('SASM_BE_DB_HOST'),
        "PORT": env('SASM_BE_DB_PORT'),
    }
}

LOGGING['loggers']['django']['handlers'].append('file')

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
