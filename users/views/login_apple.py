import jwt
import json
import random
import string

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from ..models import User
from .social_login import *
from core.exceptions import ApplicationError
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from jwt.algorithms import RSAAlgorithm

@api_view(["GET", "POST"])
@method_decorator(csrf_exempt)
@permission_classes([AllowAny])
def apple_callback(request):
    id_token = request.GET.get('token')
    
    #토큰 검증
    header = jwt.get_unverified_header(id_token)

    APPLE_PUBLIC_KEY_URL = 'https://appleid.apple.com/auth/keys'

    key_payload = requests.get(APPLE_PUBLIC_KEY_URL).json()
    keys = key_payload['keys']

    for key in keys:
        if key['kid'] == header['kid'] and key['alg'] == header['alg']:
            public_key = RSAAlgorithm.from_jwk(json.dumps(key))

    try:
        decodedToken = jwt.decode(id_token, public_key, audience='kr.co.sasm', algorithms='RS256')
    except jwt.exceptions.ExpiredSignatureError as e:
        raise ApplicationError("토큰 검증에 실패하였습니다.")
    except jwt.exceptions.InvalidAudienceError as e:
        raise ApplicationError("토큰 대상자가 일치하지 않습니다.")
    except jwt.exceptions.InvalidTokenError as e:
        raise ApplicationError("유효하지 않은 토큰입니다.")

    #사용자 정보 추출
    email = decodedToken.get("email", None)
    email_verified = decodedToken.get("email_verified", None)
    
    if not email or not email_verified:
        raise ApplicationError("이메일을 가져올 수 없거나 검증되지 않은 이메일입니다.")
    
    # 유저가 있는 경우 가져오고, 없는 경우 생성
    user_qs = User.objects.filter(email=email)
    if user_qs.exists() and user_qs.first().social_provider == 'apple':
        user = user_qs.first()
    elif user_qs.exists():  # 해당 이메일이 다른 로그인 방식을 이미 사용 중인 경우
        user = user_qs.first()
        raise ApplicationError("다른 로그인 방식을 사용 중인 이메일입니다. {} 로그인 방식을 이용해주세요.".format(
            user.social_provider if user.social_provider else 'SASM 기본'))
    else:
        nickname = None
        # 유저 초기 랜덤 닉네임 생성 (최대 10번 시도)
        for _ in range(10):
            candidate = 'user-'+''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            if not User.objects.filter(nickname=candidate).exists():
                nickname = candidate
                break

        if not nickname:
            raise ApplicationError("유효한 닉네임을 생성하지 못했습니다.")
    
        user = User(
                email=email,
                nickname=nickname,
                is_active=True,
                social_provider='apple',
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
