from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
DEBUG = False

ALLOWED_HOSTS = ['*']


sentry_sdk.init(
    dsn="https://404ba4a0e77d437e8755decbc545c8eb@o4504016282583040.ingest.sentry.io/4504016285270016",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)