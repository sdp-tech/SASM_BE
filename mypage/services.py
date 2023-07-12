import datetime
from rest_framework_jwt.settings import api_settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from core.exceptions import ApplicationError

from users.models import User
from mypage.selectors.follow_selectors import UserFollowSelector

JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER


class UserFollowService:
    def __init__(self):
        pass

    @staticmethod
    def follow_or_unfollow(source: User, target: User) -> bool:
        # 이미 팔로우 한 상태 -> 팔로우 취소 (unfollow)
        if UserFollowSelector.follows(source=source, target=target):
            source.follows.remove(target)
            return False

        else:  # 팔로우 하지 않은 상태 -> 팔로우 (follow)
            source.follows.add(target)
            return True

    def only_unfollow(source: User, target: User) -> bool:
        source.follows.remove(target)
        return False


class UserInfoService:
    def __init__(self, user: User):
        self.user = user

    def update(self,
               gender: str,
               nickname: str,
               birthdate: datetime.date,
               profile_image: InMemoryUploadedFile,
               introduction : str,
               ) -> User:
               

        if gender is not None:
            self.user.gender = gender
        # 중복된 닉네임 수정 시 reject
        if nickname is not None:
           if nickname.strip() == "":
                nickname = self.user.nickname
           elif User.objects.filter(nickname=nickname).exists():
                raise ApplicationError(
                    message="사용 중인 닉네임 전달", extra={"nickname": "이미 사용 중인 닉네임 입니다."})
           self.user.nickname = nickname
        
        if birthdate is not None:
            self.user.birthdate = birthdate
        
        if profile_image is not None:
            self.user.profile_image = profile_image

        self.user.introduction = introduction

        self.user.full_clean()
        self.user.save()

        return self.user
