from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..models import User
from .social_login import *
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from core.exceptions import ApplicationError


@api_view(["GET", "POST"])
@method_decorator(csrf_exempt)
@permission_classes([AllowAny])
def kakao_callback(request):
    rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
    code = request.GET.get("code")
    redirect_uri = 'https://www.sasm.co.kr/auth/kakao/callback/'

    # 인가 코드를 이용해 사용자 정보에 접근할 수 있는 엑세스 토큰 받아오기
    access_token_res = requests.get(
        f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={rest_api_key}&redirect_uri={redirect_uri}&code={code}"
    )
    access_token = access_token_res.json().get("access_token")

    # 받아온 엑세스 토큰으로 사용자 정보 가져오기
    profile_res = requests.get(
        'https://kapi.kakao.com/v2/user/me', headers={"Authorization": f'Bearer ${access_token}'})
    profile = profile_res.json().get('kakao_account')

    # 이메일, 닉네임 정보 가져오기
    email = profile.get('email', None)
    nickname = profile.get('profile').get('nickname', None)
    # profile_image = profile.get('profile').get('thumbnail_image_url')

    # 필수 정보인 이메일과 닉네임을 성공적으로 가져오지 못한 경우 에러 반환
    if not email or not nickname:
        raise ApplicationError("카카오로부터 이메일 또는 닉네임을 가져오지 못했습니다.")

    # 유저가 있는 경우 가져오고, 없는 경우 생성
    if User.objects.filter(email=email, social_provider='kakao').exists():
        user = User.objects.get(email=email, social_provider='kakao')
    else:
        # 해당 이메일이 다른 아이디에서 이미 사용 중인 경우
        if User.objects.filter(email=email).exists():
            raise ApplicationError("이미 사용 중인 이메일입니다.")

        user = User(
            email=email,
            nickname=nickname,
            is_active=True,
            social_provider='kakao',
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
