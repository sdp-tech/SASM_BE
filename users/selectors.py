from typing import List
from django.http import Http404, HttpResponseBadRequest
from django.db.models import QuerySet, Q
from django.contrib.auth import authenticate

from users.models import User
from places.models import Place

class UserSelector:
    def __init__(self):
        pass

    # def get_from_id(id: int) -> User:
    #     try:
    #         return User.objects.get(id__exact=id)
    #     except User.DoesNotExist:
    #         raise Http404
    #     except User.MultipleObjectsReturned:
    #         raise Http404
    
    @staticmethod
    def get_user_from_email(email: str) -> User:
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise Http404
        except User.MultipleObjectsReturned:
            raise Http404
    
    @staticmethod
    def check_password(user: User, password: str):
        return user.check_password(password)
    
    @staticmethod
    def check_email(email: str):
        return User.objects.filter(email=email).exists()
    
    @staticmethod
    def check_nickname(nickname: str):
        return User.objects.filter(nickname=nickname).exists()
    
    @staticmethod
    def get_user_like_place(user: User):
        return user.PlaceLikeUser.all()
    
    @staticmethod
    def get_user_like_story(user: User):
        return user.StoryLikeUser.all()

    @staticmethod
    def check_password_exists(email: str, password: str):
        if(authenticate(email=email, password=password) != None):
            raise HttpResponseBadRequest

    @staticmethod
    def get_user_from_code(code: str) -> User:
        try:
            return User.objects.get(code=code)
        except User.DoesNotExist:
            raise Http404
        except User.MultipleObjectsReturned:
            raise Http404

    @staticmethod
    def filter_place_by_query(filter: List, queryset: QuerySet) -> QuerySet:
        q = Q()
        for category in filter:
            q.add(Q(category=category), q.OR)

        return queryset.filter(q)
    
    @staticmethod
    def filter_story_by_query(filter: List, queryset: QuerySet) -> QuerySet:
        q = Q()
        for category in filter:
            q.add(Q(address__category=category),q.OR)

        return queryset.filter(q)



