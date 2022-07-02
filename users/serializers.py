from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import User
from .utils import (
    email_isvalid, 
    username_isvalid,
)
import traceback
from rest_framework.response import Response 
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_jwt.settings import api_settings
from django.contrib.auth.models import update_last_login

#email 인증 관련
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage

#로그인 & 이메일 인증관련
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = (
            "id",
            #"username",
            "password",
            "gender",
            "nickname",
            "birthdate",
            "email",
            "address",
            "profile_image"
        )
        read_only_fields = ("id",)

    def validate_email(self, obj):
        if email_isvalid(obj):
            return obj
        raise serializers.ValidationError('메일 형식이 올바르지 않습니다.')


    def validate_username(self, obj):
        if username_isvalid(obj):
            return obj
        raise serializers.ValidationError('닉네임은 한 글자 이상이어야 합니다.')

    def create(self, validated_data):
        #password = validated_data.get("password")
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.is_active = False
        user.save()
        payload = JWT_PAYLOAD_HANDLER(user)
        jwt_token = JWT_ENCODE_HANDLER(payload)
        message = render_to_string('users/user_activate_email.html', {
            'user': user,
            'domain': 'localhost:8000',
            'uid': force_str(urlsafe_base64_encode(force_bytes(user.pk))),
            'token': jwt_token,
        })
        print(message)
        mail_subject = '[SDP] 회원가입 인증 메일입니다'
        to_email = user.email
        email = EmailMessage(mail_subject, message, to = [to_email])
        email.send()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        # email, password에 일치하는 user가 있는지 확인
        email = data.get("email", None)
        password = data.get("password", None)
        user = authenticate(email=email, password=password)
        if user is None:
            return {
                'email': 'None'
            }

        try:
            # 토큰 발급
            payload = JWT_PAYLOAD_HANDLER(user)
            jwt_token = JWT_ENCODE_HANDLER(payload)
            update_last_login(None, user)
        
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'User with given email and password does not exist'
            )
        return {
            'email': user.email,
            'token': jwt_token
        }

#비밀번호 이메일 보낼 때 쓰는 거
class PwEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=64)

    def validate_email(self, value):
        '''데이터베이스에 존재하는지 확인'''
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("존재하지 않는 이메일입니다.")
        else:
            return value

#새로 이메일 입력 받을 때 쓰는거
class PwChangeSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    
class EmailFindSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=64,required=True)

class RepetitionCheckSerializer(serializers.Serializer):
    type = serializers.CharField(required=True,max_length=64)
    email = serializers.CharField(required=False, allow_blank=True, max_length=100)
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=100)
