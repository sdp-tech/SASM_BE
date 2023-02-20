import io
import time
import uuid

from django.conf import settings
from django.db import transaction
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import exceptions

from users.models import User
from stories.models import Story, StoryPhoto, StoryComment
from places.models import Place
from .selectors import StoryLikeSelector, StoryCommentSelector

class StoryCoordinatorService:
    def __init__(self, user: User):
        if user.is_authenticated: 
            self.user = user
        else:
            raise exceptions.ValidationError()

    def like_or_dislike(self, story_id: int) -> bool:
        if StoryLikeSelector.likes(story_id=story_id, user=self.user) == 'ok':
            # Story의 like_cnt 1 감소
            StoryService.dislike(story_id=story_id, user=self.user)
            return 'none'
        else: 
            # Story의 like_cnt 1 증가
            StoryService.like(story_id=story_id, user=self.user)
            return 'ok'


class StoryService:
    def __init__(self):
        pass

    @staticmethod
    def like(story_id: int, user: User):
        story = Story.objects.get(id=story_id)

        story.story_likeuser_set.add(user)
        story.story_like_cnt += 1
        print('좋아요 수', story.story_like_cnt)

        story.full_clean()
        story.save()
    
    @staticmethod
    def dislike(story_id: int, user: User):
        story = Story.objects.get(id=story_id)

        story.story_likeuser_set.remove(user)
        story.story_like_cnt -= 1
        print('좋아요수(dislike)', story.story_like_cnt)

        story.full_clean()
        story.save()


class StoryCommentCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, story_id: int, content: str, isParent: bool, parent_id: int, mentioned_email: str) -> StoryComment:
        story = Story.objects.get(id=story_id)
        print('2:', story)
        comment_service = StoryCommentService()
        if parent_id:
            parent = StoryComment.objects.get(id=parent_id)
        else:
            parent = None

        if mentioned_email:
            mentioned_user = User.objects.get(email=mentioned_email)
        else:
            mentioned_user = None

        print('~~~~~~~', parent, mentioned_user)
        story_comment = comment_service.create(
            story=story,
            content=content,
            isParent=isParent,
            parent=parent,
            mentioned_user=mentioned_user,
            writer=self.user
        )
        print('4:',story_comment)

        return story_comment

    @transaction.atomic
    def update(self, story_comment_id: int, content: str, mentioned_email: str) -> StoryComment:
        story_comment_service = StoryCommentService()
        story_comment_selector = StoryCommentSelector()

        # user가 해당 story_comment의 writer가 아닐 경우 에러 발생
        if not story_comment_selector.isWriter(story_comment_id=story_comment_id, user=self.user):
            raise exceptions.ValidationError({'error': '댓글 작성자가 아닙니다.'})

        if mentioned_email:
            mentioned_user = User.objects.get(email=mentioned_email)
        

        story_comment = story_comment_service.update(
            story_comment_id=story_comment_id,
            content=content,
            mentioned_user=mentioned_user,
        )

        return story_comment

    @transaction.atomic
    def delete(self, story_comment_id: int):
        story_comment_service = StoryCommentService()
        story_comment_selector = StoryCommentSelector()

        # user가 해당 story_comment의 writer가 아닐 경우 에러 발생  
        if not story_comment_selector.isWriter(story_comment_id=story_comment_id, user=self.user):
            raise exceptions.ValidationError({'error': '댓글 작성자가 아닙니다.'})

        story_comment_service.delete(story_comment_id=story_comment_id)


class StoryCommentService:
    def __init__(self):
        pass

    def create(self, story: Story, content: str, isParent: bool, parent: StoryComment, mentioned_user: User, writer: User) -> StoryComment:
        print('#', story, content)
        story_comment = StoryComment(
            story=story,
            content=content,
            isParent=isParent,
            parent=parent,
            mention=mentioned_user,
            writer=writer,
        )
        print('3:', story_comment)

        story_comment.full_clean()
        story_comment.save()

        return story_comment

    def update(self, story_comment_id: int, content: str, mentioned_user: User) -> StoryComment:
        story_comment = StoryComment.objects.get(id=story_comment_id)

        story_comment.content = content
        story_comment.mention = mentioned_user

        story_comment.full_clean()
        story_comment.save()

        return story_comment

    def delete(self, story_comment_id: int):
        story_comment = StoryComment.objects.get(id=story_comment_id)

        story_comment.delete()


