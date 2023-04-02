import os
import string
import random
from email.mime.image import MIMEImage
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string

from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_jwt.settings import api_settings

from users.models import User
from users.selectors import UserSelector

JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER


class UserService:
    def __init__(self):
        pass
    # def __init__(self, user: User):
    #     self.user = user

    # def update(self, profile_image: str, password: str, nickname: str, address: str, birthdate: str, gender: str) -> User:
    #     user = User.objects.get(id=self.user.id)

    #     user.update_profile_image(profile_image)

    #     user.full_clean()
    #     user.save()

    #     return user

    def login(self, email: str, password: str):
        user_selector = UserSelector()

        user = user_selector.get_user_from_email(email)

        if not user_selector.check_password(user, password):
            raise exceptions.ValidationError(
                {'detail': "아이디나 비밀번호가 올바르지 않습니다."})

        token = RefreshToken.for_user(user=user)
        data = {
            'email': user.email,
            'refresh': str(token),
            'access': str(token.access_token),
            'nickname': user.nickname
        }

        return data

    def logout(self, refresh: str):
        try:
            RefreshToken(refresh).blacklist()

        except TokenError:
            raise InvalidToken()

    def check_email(self, email: str):
        user_selector = UserSelector()

        check_email = user_selector.check_email(email)

        if (check_email):
            return '존재하는 이메일입니다'

        return '존재하지 않는 이메일입니다'

    def check_rep(self, type: str, value: str):
        user_selector = UserSelector()

        if (type == 'email'):
            check_email = user_selector.check_email(value)
            if (check_email):
                return '이미 사용중인 이메일입니다'
            return '사용 가능한 이메일입니다'

        if (type == 'nickname'):
            check_nickname = user_selector.check_nickname(value)
            if (check_nickname):
                return '이미 사용중인 닉네임입니다'
            return '사용 가능한 닉네임입니다'


class UserPasswordService:
    def __init__(self):
        pass

    def email_auth_string():
        LENGTH = 5
        string_pool = string.ascii_letters + string.digits
        auth_string = ""
        for i in range(LENGTH):
            auth_string += random.choice(string_pool)
        return auth_string

    def password_reset_send_email(self, email: str):
        user_selector = UserSelector()

        user = user_selector.get_user_from_email(email)

        payload = JWT_PAYLOAD_HANDLER(user)
        jwt_token = JWT_ENCODE_HANDLER(payload)
        code = UserPasswordService.email_auth_string()

        html_content = render_to_string('users/password_reset.html', {
            'user': user,
            'nickname': user.nickname,
            'uid': force_str(urlsafe_base64_encode(force_bytes(user.pk))),
            'token': jwt_token,
            'code': code,
        })

        user.code = code
        user.save()

        mail_subject = '[SDP] 비밀번호 변경 메일입니다'
        to_email = user.email
        from_email = 'sdpygl@gmail.com'
        msg = EmailMultiAlternatives(
            mail_subject, '...', from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        file_path = os.path.join(
            settings.BASE_DIR, 'static/img/SASM_LOGO_BLACK.png')
        img_data = open(file_path, 'rb').read()
        image = MIMEImage(img_data)
        image.add_header('Content-ID', '<{}>'.format('SASM_LOGO_BLACK.png'))
        msg.attach(image)

        msg.send()

    def password_change_with_code(self, code: str, password: str):
        user_selector = UserSelector
        user = user_selector.get_user_from_code(code)

        user.set_password(password)
        user.code = UserPasswordService.email_auth_string()

        user.full_clean()
        user.save()

    def password_change(self, user: User, password: str):
        user.set_password(password)

        user.full_clean()
        user.save()
