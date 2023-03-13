import io
import time
import uuid

from django.conf import settings
from django.db import transaction
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from rest_framework import exceptions

from users.models import User
from stories.models import Story, StoryComment
from places.models import Place
from .selectors import StoryLikeSelector

def check_user(user: User):
    if user.is_authenticated: 
        pass
    else:
        raise exceptions.ValidationError()


class StoryCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    def like_or_dislike(self, story_id: int) -> bool:
        check_user(self.user)
        
        if StoryLikeSelector.likes(story_id=story_id, user=self.user):
            # Story의 like_cnt 1 감소
            StoryService.dislike(story_id=story_id, user=self.user)
            return False
        else:
            # Story의 like_cnt 1 증가
            StoryService.like(story_id=story_id, user=self.user)
            return True


class StoryService:
    def __init__(self):
        pass

    @staticmethod
    def like(story_id: int, user: User):
        story = Story.objects.get(id=story_id)

        story.story_likeuser_set.add(user)
        story.story_like_cnt += 1

        story.full_clean()
        story.save()

    @staticmethod
    def dislike(story_id: int, user: User):
        story = Story.objects.get(id=story_id)

        story.story_likeuser_set.remove(user)
        story.story_like_cnt -= 1

        story.full_clean()
        story.save()