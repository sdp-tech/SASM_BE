from .base import *
DEBUG = False

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

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "TIMEOUT": 86400,  # 1 day
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
