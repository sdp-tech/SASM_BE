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
            profile_image=F('writer__profile_image'),
        ).values(
            'id',
            'story',
            'content',
            'isParent',
            'group',
            'nickname',
            'email',
            'mention',
            'profile_image',
            'created_at',
            'updated_at',
        ).order_by('group', 'id')

        return story_comments