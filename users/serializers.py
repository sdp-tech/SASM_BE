import os
from .utils import (
    email_isvalid,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import User
# email 인증 관련
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
# 로그인 & 이메일 인증관련
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
            # "username",
            "password",
            "gender",
            "nickname",
            "birthdate",
            "email",
            "address",
            "profile_image",
            "is_sdp_admin",
        )
        read_only_fields = ("id",)

    # TODO: refactor : 아래 email, nickname과 같은 도메인 로직은 model layer로 이동
    def validate_email(self, obj):
        if email_isvalid(obj):
            return obj
        raise serializers.ValidationError('메일 형식이 올바르지 않습니다.')

    def create(self, validated_data):
        # password = validated_data.get("password")
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.is_active = False
        user.save()
        payload = JWT_PAYLOAD_HANDLER(user)
        jwt_token = JWT_ENCODE_HANDLER(payload)
        plaintext = '...'
        html_content = render_to_string('users/user_activate_email.html', {
            'user': user,
            'nickname': user.nickname,
            'domain': 'api.sasmbe.com',
            'uid': force_str(urlsafe_base64_encode(force_bytes(user.pk))),
            'token': jwt_token,
        })
        print(html_content)
        mail_subject = '[SDP] 회원가입 인증 메일입니다'
        to_email = user.email
        from_email = 'sdpygl@gmail.com'
        msg = EmailMultiAlternatives(
            mail_subject, plaintext, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        imagefile = 'SASM_LOGO_BLACK.png'
        file_path = os.path.join(
            settings.BASE_DIR, 'static/img/SASM_LOGO_BLACK.png')
        img_data = open(file_path, 'rb').read()
        image = MIMEImage(img_data)
        image.add_header('Content-ID', '<{}>'.format(imagefile))
        msg.attach(image)
        msg.send()
        print('dd')
        return user


class RepetitionCheckSerializer(serializers.Serializer):
    type = serializers.CharField(required=True, max_length=64)
    email = serializers.CharField(
        required=False, allow_blank=True, max_length=100)
    nickname = serializers.CharField(
        required=False, allow_blank=True, max_length=100)
