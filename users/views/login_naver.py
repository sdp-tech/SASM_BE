from allauth.socialaccount.providers.naver import views as naver_view
from ..models import User
# 소셜 로그인 관련 설정들
from .social_login import *
from rest_framework.response import Response
from rest_framework.decorators import api_view

# random state 생성하기
state = getattr(settings, 'STATE')
STATE_LENGTH = 15
string_pool = string.ascii_letters + string.digits
for i in range(STATE_LENGTH):
    state += random.choice(string_pool)

BASE_URL = 'http://127.0.0.1:8000/'
NAVER_CALLBACK_URI = BASE_URL + 'http://127.0.0.1:3000/users/naver/callback/'

@api_view(["GET", "POST"])
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
        return Response({
                        'status': 'error',
                        'message': 'JSON_DECODE_ERROR',
                        'code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
        
    access_token = token_req_json.get("access_token")

    profile_request = requests.get("https://openapi.naver.com/v1/nid/me", headers={"Authorization" : f"Bearer {access_token}"},)
    profile_json = profile_request.json().get('response')
    email = profile_json.get('email', None)
    nickname = profile_json.get('nickname', None)

    try:
        user = User.objects.get(email=email)
        social_user = SocialAccount.objects.get(user=user)
        if social_user is None:
            return Response({
                        'status': 'error',
                        'message': 'Email exists but not social user',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
        if social_user.provider != 'naver':
            return Response({
                        'status': 'error',
                        'message': 'Social type does not match',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
            
        data = {'access_token': access_token, 'code': code}
        accept = requests.post(
            f"{BASE_URL}users/naver/login/finish/", data=data
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
            f"{BASE_URL}users/naver/login/finish/", data=data
        )
        accept_status = accept.status_code
        if accept_status != 200:
            return Response({
                        'status': 'error',
                        'message': 'Failed to signup',
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

class NaverLogin(SocialLoginView):
    adapter_class = naver_view.NaverOAuth2Adapter
    client_class = OAuth2Client
    callback_url = NAVER_CALLBACK_URI