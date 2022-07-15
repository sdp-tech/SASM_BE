from ..models import User
from django.shortcuts import redirect
from rest_framework import status

#소셜 로그인 관련 설정들
import requests
import string
import random
from django.conf import settings
from django.http import JsonResponse
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.naver import views as naver_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from json.decoder import JSONDecodeError
from dj_rest_auth.registration.views import SocialLoginView

# random state 생성하기
state = getattr(settings, 'STATE')
STATE_LENGTH = 15
string_pool = string.ascii_letters + string.digits
for i in range(STATE_LENGTH):
    state += random.choice(string_pool)

BASE_URL = 'http://127.0.0.1:8000/'
NAVER_CALLBACK_URI = BASE_URL + 'users/naver/callback/'


# 네이버 소셜 로그인
def naver_login(request):
    client_id = getattr(settings, "NAVER_CLIENT_ID")
    return redirect(
       f"https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id={client_id}&state={state}&redirect_uri={NAVER_CALLBACK_URI}"
    )

def naver_callback(request):
    client_id = getattr(settings, 'NAVER_CLIENT_ID')
    client_secret = getattr(settings, "NAVER_SECRET_KEY")
    code = request.GET.get("code")
    
    token_req = requests.get(
        f"https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&client_id={client_id}&client_secret={client_secret}&code={code}&state={state}"
    )

    token_req_json = token_req.json()
    error = token_req_json.get("error")
    if error is not None:
        raise JSONDecodeError(error)
    access_token = token_req_json.get("access_token")

    profile_request = requests.get("https://openapi.naver.com/v1/nid/me", headers={"Authorization" : f"Bearer {access_token}"},)
    profile_json = profile_request.json()
    email = profile_json.get('email', None)

    try:
        user = User.objects.get(email=email)
        social_user = SocialAccount.objects.get(user=user)
        if social_user is None:
            return JsonResponse(
                {'err_msg': 'email exists but not social user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if social_user.provider != 'naver':
            return JsonResponse(
                {'err_msg': 'no matching social type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = {'access_token': access_token, 'code': code}
        accept = requests.post(
            f"{BASE_URL}users/naver/login/finish", data=data
        )
        accept_status = accept.status_code
        if accept_status != 200:
            return JsonResponse(
                {'err_msg': 'failed to signin'},
                status=accept_status
            )
        accept_json = accept.json()
        accept_json.pop('user', None)
        return JsonResponse(accept_json)
    except User.DoesNotExist:
        data = {'access_token': access_token, 'code': code}
        accept = requests.post(
            f"{BASE_URL}users/naver/login/finish/", data=data
        )
        accept_status = accept.status_code
        if accept_status != 200:
            return JsonResponse(
                {'err_msg': 'failed to signup'},
                status=accept_status
            )
        accept_json = accept.json()
        accept_json.pop('user', None)
        return JsonResponse(accept_json)

class NaverLogin(SocialLoginView):
    adapter_class = naver_view.NaverOAuth2Adapter
    client_class = OAuth2Client
    callback_url = NAVER_CALLBACK_URI