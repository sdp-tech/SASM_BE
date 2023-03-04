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
from .selectors import StoryCommentSelector


class StoryCommentCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def update(self, story_comment_id: int, content: str, mentioned_email: str) -> StoryComment:
        story_comment_service = StoryCommentService()
        story_comment_selector = StoryCommentSelector()
        # user가 해당 story_comment의 writer가 아닐 경우 에러 발생
        if not story_comment_selector.isWriter(story_comment_id=story_comment_id, user=self.user):
            raise exceptions.ValidationError({'error': '댓글 작성자가 아닙니다.'})
        
        if mentioned_email:
            mentioned_user = User.objects.get(email=mentioned_email)
        else:
            mentioned_user = None
        
        story_comment = story_comment_service.update(
            story_comment_id=story_comment_id,
            content=content,
            mentioned_user=mentioned_user,
        )
        return story_comment
    
class StoryCommentService:
    def __init__(self):
        pass

    def update(self, story_comment_id: int, content: str, mentioned_user: User) -> StoryComment:
        story_comment = StoryComment.objects.get(id=story_comment_id)
        story_comment.content = content
        story_comment.mention = mentioned_user

        story_comment.full_clean()
        story_comment.save()
        
        return story_comment
