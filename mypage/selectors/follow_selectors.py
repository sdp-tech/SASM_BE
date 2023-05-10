from users.models import User

class UserFollowSelector:
    def __init__(self):
        pass

    @staticmethod
    def follows(source: User, target: User):
        return source.follows.contains(target)

    @staticmethod
    def get_following(source: User):
        return source.follows.all()

    @staticmethod
    def get_follower(target: User):
        return target.followers.all()
    
    @staticmethod
    def get_following_with_filter(source_email: str, target_email: str):
        following = User.objects.all()
        if source_email:
            following = User.objects.filter(email__icontains=source_email)

        if target_email:
            following = following.filter(followers__email__icontains=target_email)

        return following
    
    def get_follower_with_filter(source_email: str, target_email: str):
        follower = User.objects.all()

        if source_email:
            follower = follower.filter(email__icontains=source_email)

        if target_email:
            follower = follower.filter(follows__email__icontains=target_email)

        return follower