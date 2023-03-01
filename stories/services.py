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


class StoryCoordinatorService:
    def __init__(self, user: User):
        if user.is_authenticated: 
            self.user = user
        else:
            raise exceptions.ValidationError()

    def like_or_dislike(self, story_id: int) -> bool:
        if StoryLikeSelector.likes(story_id=story_id, user=self.user) == True:
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