#소셜 로그인 관련 설정들
import requests
import string
import random
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework import status
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from json.decoder import JSONDecodeError
from dj_rest_auth.registration.views import SocialLoginView