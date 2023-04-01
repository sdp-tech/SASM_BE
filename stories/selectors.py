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


@dataclass
class StoryDto:
    id: int
    title: str
    place_name: str
    story_review: str
    html_content: str
    tag: str
    views: int
    story_like: str
    category: int
    semi_category: str
    writer: str
    writer_is_verified: bool


class StoryCoordinatorSelector:
    def __init__(self, user: User):
        self.user = user

    def detail(self, story_id: int):
        story = StorySelector.detail(story_id=story_id)

        story_like = StoryLikeSelector.likes(
            story_id=story.id,
            user=self.user,
        )
        semi_cate = semi_category(story.id)

        dto = StoryDto(
            id=story.id,
            title=story.title,
            place_name=story.place_name,
            story_review=story.story_review,
            html_content=story.html_content,
            tag=story.tag,
            views=story.views,
            story_like=story_like,
            category=story.category,
            semi_category=semi_cate,
            writer=story.writer,
            writer_is_verified=story.writer.is_verified
        )
        return dto


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

    def detail(story_id: int, extra_fields: dict = {}):
        return Story.objects.annotate(
            place_name=F('address__place_name'),
            category=F('address__category'),
            **extra_fields
        ).get(id=story_id)

    def recommend_list(story_id: int):
        story = Story.objects.get(id=story_id)
        q = Q(address__category=story.address.category)
        recommend_story = Story.objects.filter(q).exclude(id=story_id).annotate(
            writer_is_verified=F('writer__is_verified')
        )

        return recommend_story

    @staticmethod
    def list(search: str = '', latest: bool = True):
        q = Q()
        q.add(Q(title__icontains=search) | Q(
            address__place_name__icontains=search), q.AND)  # 스토리 제목 또는 내용 검색

        # 최신순 정렬
        if latest:
            order = '-created'
        else:
            order = 'created'

        story = Story.objects.filter(q).annotate(
            place_name=F('address__place_name'),
            category=F('address__category'),
            writer_is_verified=F('writer__is_verified')
        ).order_by(order)

        return story


class StoryLikeSelector:
    def __init__(self):
        pass

    @staticmethod
    def likes(story_id: int, user: User):
        story = get_object_or_404(Story, pk=story_id)
        # 좋아요가 존재하는 지 안하는 지 확인
        if story.story_likeuser_set.filter(pk=user.pk).exists():
            return True
        else:
            return False


class MapMarkerSelector:
    def __init__(self, user: User):
        self.user = user

    @staticmethod
    def map(story_id: int):
        story = Story.objects.get(id=story_id)
        place = story.address

        return place


class StoryCommentSelector:
    def __init__(self):
        pass

    def isWriter(self, story_comment_id: int, user: User):
        return StoryComment.objects.get(id=story_comment_id).writer == user

    @staticmethod
    def list(story_id: int):
        story = Story.objects.get(id=story_id)
        q = Q(story=story)

        story_comments = StoryComment.objects.filter(q).annotate(
            nickname=F('writer__nickname'),
            email=F('writer__email'),
            profile_image=F('writer__profile_image'),
        ).values(
            'id',
            'story',
            'content',
            'nickname',
            'email',
            'mention',
            'profile_image',
            'created_at',
            'updated_at',
        ).order_by('id')

        return story_comments
