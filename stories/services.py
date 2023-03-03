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
# from .selectors import StoryLikeSelector, StoryCommentSelector


class StoryCommentCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, story_id: int, content: str, isParent: bool = True, parent_id: int = None, mentioned_email: str = '') -> StoryComment:
        story = Story.objects.get(id=story_id)

        comment_service = StoryCommentService()
        
        if parent_id:
            parent = StoryComment.objects.get(id=parent_id)
        else:
            parent = None

        if mentioned_email:
            mentioned_user = User.objects.get(email=mentioned_email)
        else:
            mentioned_user = None

        story_comment = comment_service.create(
            story=story,
            content=content,
            isParent=isParent,
            parent=parent,
            mentioned_user=mentioned_user,
            writer=self.user
        )

        return story_comment


class StoryCommentService:
    def __init__(self):
        pass

    def create(self, story: Story, content: str, isParent: bool, parent: StoryComment, mentioned_user: User, writer: User) -> StoryComment:
        story_comment = StoryComment(
            story=story,
            content=content,
            isParent=isParent,
            parent=parent,
            mention=mentioned_user,
            writer=writer,
        )

        story_comment.full_clean()
        story_comment.save()
        
        return story_comment