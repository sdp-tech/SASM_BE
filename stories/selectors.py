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
    title: str
    place_name: str
    story_review: str
    html_content: str
    tag: str
    likeCount: int
    viewCount: int
    likes: bool
    created: datetime
    updated: datetime

    category: int
    vegan_category: str
    tumblur_category: str
    reusable_con_category: str
    pet_category :str

    # photoList: list[str] = None   


class StoryCoordinatorSelector:
    def __init__(self, user: User):
        self.user = user

    def list(self, query: str, latest: bool):
        extra_fields = {}
        story = StorySelector.list(query=query, latest=latest, extra_fields=extra_fields)
        print('~~~~', story)

        return StorySelector.list(
            query=query,
            latest=latest,
            extra_fields=extra_fields
        )

    def detail(self, story_id: int):
        story = StorySelector.detail(story_id=story_id)

        likes = StoryLikeSelector.likes(
            story_id=story.id,
            user=self.user
        )

        dto = StoryDto(
            title=story.title,
            place_name=story.place_name,
            story_review=story.story_review,
            html_content=story.html_content,
            tag=story.tag,
            likeCount=story.likeCount,
            viewCount=story.viewCount,
            likes=likes,
            created=story.created,
            updated=story.updated,
            category=story.category,
            vegan_category=story.vegan_category,
            tumblur_category=story.tumblur_category,
            reusable_con_category=story.reusable_con_category,
            pet_category=story.pet_category,
        )

        return dto

class StorySelector:
    def __init__(self):
        pass

    # def isWriter(self, story_id: int, user: User):
    #     return Story.objects.get(id=story_id).writer == user

    @staticmethod
    def list(query: str = '', latest: bool = True, extra_fields: dict = {}):
        print('list')
        print('query', query)
        print('latest', latest)
        q = Q()
        q.add(Q(title__icontains=query) | Q(address__place_name__icontains=query), q.AND)  #스토리 제목 또는 내용 검색

        #최신순 정렬
        if latest:
            order = '-created'
        else:
            order = 'created'

        story = Story.objects.filter(q).annotate(
            place_name=F('address__place_name'),
            category=F('address__category'),
            vegan_category=F('address__vegan_category'),
            tumblur_category=F('address__tumblur_category'),
            reusable_con_category=F('address__reusable_con_category'),
            pet_category=F('address__pet_category'),
            likeCount=F('story_like_cnt'),
            likes=F('story_likeuser_set'),
            **extra_fields
        ).order_by(order)

        return story

    @staticmethod
    def detail(story_id: int, extra_fields: dict = {}):
        print('!!')
        return Story.objects.annotate(
            place_name=F('address__place_name'),
            category=F('address__category'),
            vegan_category=F('address__vegan_category'),
            tumblur_category=F('address__tumblur_category'),
            reusable_con_category=F('address__reusable_con_category'),
            pet_category=F('address__pet_category'),
            likeCount=F('story_like_cnt'),
            viewCount=F('views'),
            **extra_fields
        ).get(id=story_id)


class StoryLikeSelector:
    def __init__(self):
        pass

    @staticmethod
    def likes(story_id: int, user: User):
        # print('story_id', story_id)
        # print('user', user)
        story = get_object_or_404(Story, pk=story_id)
        # print('story',story)
        # print('user.pk', user.pk)
        # print('kk',story.story_likeuser_set.filter(pk=user.pk).exists())
        return story.story_likeuser_set.filter(
            pk=user.pk
        ).exists()  #좋아요가 존재하는 지 안하는 지 확인


# class StoryCommentCoordinatorSelector:
#     def __init__(self, user: User):
#         self.user = user

#     def list(self, story_id: int):
#         story = Story.objects.get(id=story_id)


class StoryCommentSelector:
    def __init__(self):
        pass

    def isWriter(self, story_comment_id: int, user: User):
        return StoryComment.objects.get(id=story_comment_id).writer == user

    @staticmethod
    def list(self, story_id: int):
        story = Story.objects.get(id=story_id)
        q = Q(story=story)

        story_comments = Story.objects.filter(q).annotate(
            # 댓글이면 id값을, 대댓글이면 parent id값을 대표값(group)으로 설정
            # group 내에서는 id값 기준으로 정렬
            group=Case(
                When(
                    isParent=False,
                    then='parent_id'
                ),
                default='id'
            ),
            nickname=F('writer__nickname'),
            email=F('writer__email'),
            mentionEmail=F('mention__email'),
            mentionNickname=F('mention__nickname'),
            profile_image=F('writer__profile_image'),
        ).values(
            'story',
            'content',
            'isParent',
            'group',
            'nickname',
            'email',
            'mentionEmail',
            'mentionNickname',
            'profile_image',
            'created',
            'updated',
        ).order_by('group', 'id')

        return story_comments


class MapMarkerSelector:
    def __init__(self, user: User):
        self.user = user

    @staticmethod
    def map(story_id: int):
        story = Story.objects.get(id=story_id)
        print('story: ', story)
        place = story.address
        print('place: ', place)

        return place