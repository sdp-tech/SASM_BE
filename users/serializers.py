import os
from .models import User
from .utils import (
    email_isvalid, 
    username_isvalid,
)
from django import template
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.staticfiles import finders
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.exceptions import InvalidToken

#email 인증 관련
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
#로그인 & 이메일 인증관련
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(use_url=True)
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
            "profile_image",
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
        plaintext  = '...'
        html_content = render_to_string('users/user_activate_email.html', {
            'user': user,
            'nickname' : user.nickname,
            'domain': 'localhost:8000',
            'uid': force_str(urlsafe_base64_encode(force_bytes(user.pk))),
            'token': jwt_token,
        })
        print(html_content)
        mail_subject = '[SDP] 회원가입 인증 메일입니다'
        to_email = user.email
        from_email = 'lina19197@daum.net'
        msg = EmailMultiAlternatives(mail_subject,plaintext,from_email,[to_email])
        msg.attach_alternative(html_content,"text/html")
        imagefile = 'SASM_LOGO_BLACK.png'
        file_path = os.path.join(settings.BASE_DIR,'static/img/SASM_LOGO_BLACK.png')
        img_data = open(file_path,'rb').read()
        image = MIMEImage(img_data)
        image.add_header('Content-ID','<{}>'.format(imagefile))
        msg.attach(image)
        msg.send()
        print('dd')
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=128, write_only=True)
    nickname = serializers.CharField(max_length=20, read_only=True)

    class Meta(object):
        model = User
        fields = ('email', 'password', 'nickname')
    def validate(self, data):
        # email, password에 일치하는 user가 있는지 확인
        email = data.get("email", None)
        password = data.get("password", None)
        
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)

            if not user.check_password(password):
                raise serializers.ValidationError("Email과 password가 틀렸습니다.")

        else:
            raise serializers.ValidationError("존재하지 않는 email입니다.")

        # token 발급
        token = RefreshToken.for_user(user=user)
        data = {
            'email': user.email,
            'refresh': str(token),
            'access': str(token.access_token),
            'nickname': user.nickname
        }
        # update_last_login(None, user)
        return data

class UserLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    
    default_error_messages = {
        'token_not_valid': ('Token is invalid or expired')
    }

    def validate(self, attrs):
        self.token = attrs['refresh']

        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise InvalidToken()


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
    code = serializers.CharField(max_length=5)
    password = serializers.CharField(required=True)
    
class EmailFindSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=64,required=True)

class RepetitionCheckSerializer(serializers.Serializer):
    type = serializers.CharField(required=True,max_length=64)
    email = serializers.CharField(required=False, allow_blank=True, max_length=100)
    nickname = serializers.CharField(required=False, allow_blank=True, max_length=100)
