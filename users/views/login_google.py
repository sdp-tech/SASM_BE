from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from ..models import User
from .social_login import *
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(["GET", "POST"])
@method_decorator(csrf_exempt)
@permission_classes([AllowAny])
def google_callback(request):
    access_token = request.GET.get('access_token')
    user_info_req = requests.get(
        f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
    )

    # 토큰을 이용해 사용자 정보를 가져오지 못했을 경우
    if user_info_req.status_code != 200:
        return Response({
                        'status': 'error',
                        'message': 'failed to get email',
                        'code': 400
                        }, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 정보 추출
    user_info = user_info_req.json()
    email = user_info.get('email', None)
    nickname = user_info.get('name', None)
    # profile_image = user_info.get('picture', None)

    # 필수 정보인 이메일과 닉네임을 성공적으로 가져오지 못한 경우 에러 반환
    if not email or not nickname:
        return Response({
            'status': 'error',
            'message': 'failed to get user email or nickname',
            'code': 400
        }, status=status.HTTP_400_BAD_REQUEST)

    # 유저가 있는 경우 가져오고, 없는 경우 생성
    if User.objects.filter(email=email, social_provider='google').exists():
        user = User.objects.get(email=email, social_provider='google')
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
            social_provider='google',
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
