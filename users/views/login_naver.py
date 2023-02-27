from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny

from allauth.socialaccount.providers.naver import views as naver_view

from ..models import User
# 소셜 로그인 관련 설정들
from .social_login import *

# random state 생성하기
state = getattr(settings, 'STATE')
STATE_LENGTH = 15
string_pool = string.ascii_letters + string.digits
for i in range(STATE_LENGTH):
    state += random.choice(string_pool)

BASE_URL = 'http://127.0.0.1:8000/'
NAVER_CALLBACK_URI = BASE_URL + 'http://127.0.0.1:3000/users/naver/callback/'


@api_view(["GET", "POST"])
@method_decorator(csrf_exempt)
@permission_classes([AllowAny])
def naver_callback(request):
    client_id = getattr(settings, 'NAVER_CLIENT_ID')
    client_secret = getattr(settings, "NAVER_SECRET_KEY")

    # 유저가 권한 승인하지 않은 경우
    if 'code' not in request.GET:
        return Response({
            'status': 'error',
            'message': 'user canceled the authorization process',
            'code': 400
        }, status=status.HTTP_400_BAD_REQUEST)

    # 유저가 권한 승인한 경우
    code = request.GET.get('code')

    # 네이버 계정 정보를 가져오기 위한 액세스 토큰 요청
    provider_token_response = requests.get(
        f"https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&client_id={client_id}&client_secret={client_secret}&code={code}&state={state}"
    ).json()

    if 'error' in provider_token_response:
        return Response({
            'status': 'error',
            'message': 'failed to get user access token from provider',
            'code': 400
        }, status=status.HTTP_400_BAD_REQUEST)

    # 액세스 토큰을 이용해 유저 정보 가져오기
    access_token = provider_token_response.get("access_token")
    user_info_response = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"}).json().get('response')

    email = user_info_response.get('email', None)
    nickname = user_info_response.get('nickname', None)

    # 필수 정보인 이메일과 닉네임을 성공적으로 가져오지 못한 경우 에러 반환
    if not email or not nickname:
        return Response({
            'status': 'error',
            'message': 'failed to get user email or nickname',
            'code': 400
        }, status=status.HTTP_400_BAD_REQUEST)

    # 유저가 있는 경우 가져오고, 없는 경우 생성
    if User.objects.filter(email=email, social_provider='naver').exists():
        user = User.objects.get(email=email, social_provider='naver')
    else:
        # 해당 이메일이 다른 아이디에서 이미 사용 중인 경우
        if User.objects.filter(email=email).exists():
            return Response({
                'status': 'error',
                'message': 'email is already in use',
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User(
            email=email,
            nickname=nickname,
            is_active=True,
            social_provider='naver',
            password=User.objects.make_random_password(20),
        )

        user.full_clean()
        user.save()

    token = RefreshToken.for_user(user=user)
    data = {
        'email': user.email,
        'refresh': str(token),
        'access': str(token.access_token),
        'nickname': user.nickname
    }

    return Response({
        'status': 'success',
        'data': data
    }, status=status.HTTP_200_OK)
