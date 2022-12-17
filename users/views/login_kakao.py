from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from allauth.socialaccount.providers.kakao import views as kakao_view
from ..models import User
from .social_login import *
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

import logging

BASE_URL = 'https://api.sasm.co.kr/'
KAKAO_CALLBACK_URI = 'https://www.sasm.co.kr/users/kakao/callback/'

# logger 설정
logger = logging.getLogger("login_kakao")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)

# 카카오 소셜 로그인 - 토큰 요청
@api_view(["GET", "POST"])
@method_decorator(csrf_exempt)
@permission_classes([AllowAny])
def kakao_callback(request):
    rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
    code = request.GET.get("code")
    redirect_uri = KAKAO_CALLBACK_URI
    
    token_req = requests.get(
        f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={rest_api_key}&redirect_uri={redirect_uri}&code={code}"
    )

    token_req_json = token_req.json()
    error = token_req_json.get("error")

    if error is not None:
        return Response({
                        'status': 'error',
                        'message': 'JSON_DECODE_ERROR',
                        'code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
        
    access_token = token_req_json.get("access_token")

    profile_request = requests.get('https://kapi.kakao.com/v2/user/me', headers={"Authorization": f'Bearer ${access_token}'})
    profile_json = profile_request.json()
    
    kakao_account = profile_json.get('kakao_account')

    # 이메일 외에도 프로필 이미지, 배경 이미지 url 등 가져올 수 있음
    email = kakao_account.get('email', None)
    profile = kakao_account.get('profile', None)
    nickname = profile.get('nickname', None)
    
    try:
        user = User.objects.get(email=email)
        social_user = SocialAccount.objects.get(user=user)
        if social_user is None:
            return Response({
                        'status': 'error',
                        'message': 'Email exists but not social user',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
        if social_user.provider != 'kakao':
            return Response({
                        'status': 'error',
                        'message': 'Social type does not match',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
            
        data = {'access_token': access_token, 'code': code}
        
        accept = requests.post(
            f"{BASE_URL}users/kakao/login/finish/", data=data
        )
        accept_status = accept.status_code
        
        if accept_status != 200:
            return Response({
                        'status': 'error',
                        'message': 'Failed to signin',
                        'code': accept_status
                    }, status=accept_status)
        accept_json = accept.json()
        accept_json.pop('user', None)
        response = {
                'access': accept_json.get('access_token'),
                'refresh': accept_json.get('refresh_token'),
                'nickname' : nickname
            }
        
        return Response({
                    'status': 'success',
                    'data': response,
                }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        data = {'access_token': access_token, 'code': code}
        
        accept = requests.post(
                f"{BASE_URL}users/kakao/login/finish/", data=data
            )
        
        accept_status = accept.status_code
        
        if accept_status != 200:
            return Response({
                        'status': 'error',
                        'message': 'Failed to signup',
                        'code': accept_status
                    }, status=accept_status)
        
        user = User.objects.get(email=email)
        user.is_active = True
        user.nickname = nickname
        user.save()
        
        accept_json = accept.json()
        accept_json.pop('user', None)
    
        response = {
                'access': accept_json.get('access_token'),
                'refresh': accept_json.get('refresh_token'),
                'nickname' : nickname
            }
        
        return Response({
                    'status': 'success',
                    'data': response,
                }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class KakaoLogin(SocialLoginView):
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = KAKAO_CALLBACK_URI