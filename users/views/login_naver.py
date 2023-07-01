from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny

from allauth.socialaccount.providers.naver import views as naver_view

from ..models import User
from core.exceptions import ApplicationError
# 소셜 로그인 관련 설정들
from .social_login import *

# random state 생성하기
state = getattr(settings, 'STATE')
STATE_LENGTH = 15
string_pool = string.ascii_letters + string.digits
for i in range(STATE_LENGTH):
    state += random.choice(string_pool)


@api_view(["GET", "POST"])
@method_decorator(csrf_exempt)
@permission_classes([AllowAny])
def naver_callback(request):
    if 'access_token' not in request.GET:
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

        access_token = provider_token_response.get("access_token")
    else:
        access_token = request.GET.get('access_token')

    # 액세스 토큰을 이용해 유저 정보 가져오기
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
    user_qs = User.objects.filter(email=email)
    if user_qs.exists() and user_qs.first().social_provider == 'naver':
        user = user_qs.first()
    elif user_qs.exists():  # 해당 이메일이 다른 로그인 방식을 이미 사용 중인 경우
        user = user_qs.first()
        raise ApplicationError("다른 로그인 방식을 사용 중인 이메일입니다. {} 로그인 방식을 이용해주세요.".format(
            user.social_provider if user.social_provider else 'SASM 기본'))
    else:
        user = User(
            email=email,
            nickname=nickname,
            is_active=True,
            social_provider='naver',
            password=User.objects.make_random_password(20),
        )

        user.full_clean()
        user.save()

    # 로그인 수행
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
