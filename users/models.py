import re
from email.policy import default
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import UserManager, PermissionsMixin
from .utils import (
    email_isvalid,
)
# username으로 email을 사용하기 위해 UserManager의 함수를 overrinding 한다.

# def validate_email_form(target: str):
#     validation = re.compile(
#             r'^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
#     return not re.match(validation, target)


class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(('THe Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


def user_type_is_valid(self):

    sdp_admin_user = self.is_sdp_admin and not self.is_verified
    verified_user = not self.is_sdp_admin and self.is_verified
    general_user = not self.is_sdp_admin and not self.is_verified

    return sdp_admin_user | verified_user | general_user


class User(AbstractBaseUser, PermissionsMixin):
    """custom user model"""
    username = None
    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_OTHER = "other"
    GENDER_CHOICES = (
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
        (GENDER_OTHER, "Other"),
    )
    code = models.CharField(max_length=5, blank=True)
    gender = models.CharField(choices=GENDER_CHOICES,
                              max_length=10, blank=True)
    nickname = models.CharField(max_length=20, blank=True)
    birthdate = models.DateField(blank=True, null=True)
    email = models.EmailField(max_length=64, unique=True)
    address = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(
        upload_to='profile/%Y%m%d/', default='user_profile_image.png')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(
        default=False)
    is_active = models.BooleanField(default=False)
    is_sdp_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    introduction = models.TextField(blank=True)


    # 소셜 계정인 경우, 소셜 ID 프로바이더 값 저장(ex. kakao, naver, google)
    social_provider = models.CharField(max_length=30, blank=True)

    follows = models.ManyToManyField(
        "users.User", related_name='followers', blank=True)
    
    semi_categories = models.ManyToManyField("forest.SemiCategory", related_name='semi_category', blank=True)
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

#     # 닉네임 규칙 등과 같은 도메인 지식, 로직은 Model쪽에 작성
#     def clean(self, *args, **kwargs):
#         # 닉네임 규칙 1. 공백 문자 사용 불가
#         self.nickname = self.nickname.replace(' ', '')

#         # 닉네임 규칙 2. 닉네임 길이는 2 이상
#         if len(self.nickname) < 2:
#             print(self.nickname, len(self.nickname))
#             raise ValidationError('닉네임은 두 글자 이상이어야 합니다(공백 사용 불가).')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    def clean(self):
        if not email_isvalid(self.email):
            raise ValidationError('메일 형식이 올바르지 않습니다.')
        if not user_type_is_valid(self):
            raise ValidationError('유저 타입이 잘못되었습니다.')
