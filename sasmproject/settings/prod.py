from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
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

sentry_sdk.init(
    dsn="https://404ba4a0e77d437e8755decbc545c8eb@o4504016282583040.ingest.sentry.io/4504016285270016",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated", ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
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
