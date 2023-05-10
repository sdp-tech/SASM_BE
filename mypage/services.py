from rest_framework_jwt.settings import api_settings

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
