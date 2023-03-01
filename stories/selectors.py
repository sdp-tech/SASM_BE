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