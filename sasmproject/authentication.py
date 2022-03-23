import jwt, os, time, datetime
from django.conf import settings
from rest_framework import authentication
from users.models import User


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        try:
            token = request.META.get("HTTP_AUTHORIZATION")
            if token is None:
                return None
            xjwt, jwt_token = token.split(" ")
            decoded = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
            #토큰만료 데이터
            #expire = decoded.get("exp")
            #현재시간
            #cur_date = int(time.time())
            #토큰 만료처리
            '''if cur_date > expire:
                return None'''
            pk = decoded.get("pk")
            #유저 객체
            '''user_id = decoded.get("user_id")
            if not user_id:
                return None'''
            user = User.objects.get(pk=pk)
            return (user, None)
        except (ValueError, jwt.exceptions.DecodeError, User.DoesNotExist):
            return None