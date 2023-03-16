from datetime import datetime
from dataclasses import dataclass
from collections import Counter
from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Aggregate, Value, CharField, Case, When
from django.db.models.functions import Concat, Substr
from users.models import User
from stories.models import Story, StoryPhoto, StoryComment

def semi_category(story_id: int):
    '''
        스토리의 세부 category를 알려 주기 위한 함수
    '''
    story = get_object_or_404(Story, id=story_id)
    place = story.address
    result = []
    vegan = place.vegan_category
    if vegan != '':
        result.append(vegan)
    tumblur = place.tumblur_category
    if tumblur == True:
        tumblur = '텀블러 사용 가능'
        result.append(tumblur)
    reusable = place.reusable_con_category
    if reusable == True:
        reusable = '용기내 가능'
        result.append(reusable)
    pet = place.pet_category
    if pet == True:
        pet = '반려동물 출입 가능'
        result.append(pet)
    cnt = len(result)
    ret_result = ""
    for i in range(cnt):
        if i == cnt - 1:
            ret_result = ret_result + result[i]
        else:
            ret_result = ret_result + result[i] + ', '
    return ret_result


class StorySelector:
    def __init__(self):
        pass

    @staticmethod
    def list(search: str = '', latest: bool = True):
        q = Q()
        q.add(Q(title__icontains=search) | Q(address__place_name__icontains=search), q.AND)  #스토리 제목 또는 내용 검색

        #최신순 정렬
        if latest:
            order = '-created'
        else:
            order = 'created'

        story = Story.objects.filter(q).annotate(
            place_name=F('address__place_name'),
            category=F('address__category'),
        ).order_by(order)

        return story
    

class StoryLikeSelector:
    def __init__(self):
        pass

    @staticmethod
    def likes(story_id: int, user: User):
        story = get_object_or_404(Story, pk=story_id)
        if story.story_likeuser_set.filter(pk=user.pk).exists():  #좋아요가 존재하는 지 안하는 지 확인
            return True
        else:
            return False