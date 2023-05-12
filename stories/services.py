import io
import time
import uuid

from django.conf import settings
from django.db import transaction
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from rest_framework import exceptions
from django.shortcuts import get_object_or_404

from users.models import User
from stories.models import Story, StoryComment, StoryPhoto, StoryMap
from places.models import Place
from .selectors import StoryLikeSelector, StoryCommentSelector, semi_category
from core.map_image import Marker, get_static_naver_image


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

    @transaction.atomic
    def create(self,
               title: str,
               writer: User,
               place_id: int,
               preview: str,
               tag: str,
               story_review: str,
               html_content: str,
               rep_pic: InMemoryUploadedFile,
               photoList: list[str]) -> Story:
        place = Place.objects.get(id__exact=place_id)

        service = StoryService()
        story = service.create(
            title=title,
            writer=writer,
            place=place,
            preview=preview,
            tag=tag,
            story_review=story_review,
            html_content=html_content,
            rep_pic=rep_pic,
        )

        story.save()

        # 스토리 이전에 생성된 StoryPhoto와 연결
        StoryPhotoService.process_after_story_creation(story=story,
                                                       photoList=photoList)

        # 스토리 맵 이미지 생성
        StoryMapService.create(story)

        return story

    @transaction.atomic
    def update(self,
               story: Story,
               title: str,
               story_review: str,
               tag: str,
               preview: str,
               html_content: str,
               rep_pic: InMemoryUploadedFile,
               photoList: list[str]) -> Story:
        service = StoryService()

        story = service.update(
            story=story,
            title=title,
            story_review=story_review,
            tag=tag,
            preview=preview,
            html_content=html_content,
            rep_pic=rep_pic,
        )

        # 연관 스토리 photo와의 연결 업데이트
        StoryPhotoService.process_after_story_update(story=story,
                                                     photoList=photoList)

        return story

    @transaction.atomic
    def delete(self, story: Story):
        service = StoryService()
        service.delete(story=story)


class StoryPhotoService:
    def __init__(self):
        pass

    def create(self, caption: str, image: InMemoryUploadedFile, place_id: int):
        ext = image.name.split(".")[-1]
        file_path = '{}/{}.{}'.format(place_id,
                                      'content' + str(time.time())+str(uuid.uuid4().hex), ext)
        image = ImageFile(io.BytesIO(image.read()), name=file_path)
        photo = StoryPhoto(caption=caption, image=image)
        photo.save()

        return photo

    @staticmethod
    def process_after_story_creation(story: Story, photoList: list[str]):
        if len(photoList) > 0:
            photoList = list(
                map(lambda x: x.replace(settings.MEDIA_URL, ''), photoList))
            StoryPhoto.objects.filter(
                image__in=photoList).update(story=story)

    @staticmethod
    def process_after_story_update(story: Story, photoList: list[str]):
        if len(photoList) > 0:
            photoList = list(
                map(lambda x: x.replace(settings.MEDIA_URL, ''), photoList))

        # 새롭게 추가된 포토들을 스토리와 연결
        StoryPhoto.objects.filter(
            image__in=photoList).update(story=story)


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

    def create(self,
               title: str,
               writer: User,
               place: Place,
               preview: str,
               tag: str,
               story_review: str,
               html_content: str,
               rep_pic: InMemoryUploadedFile) -> Story:
        story = Story(
            title=title,
            writer=writer,
            place=place,
            preview=preview,
            tag=tag,
            story_review=story_review,
            html_content=html_content,
            rep_pic=rep_pic,
        )
        story.full_clean()
        story.save()

        return story

    def update(self,
               story: Story,
               title: str,
               preview: str,
               tag: str,
               story_review: str,
               html_content: str,
               rep_pic: InMemoryUploadedFile) -> Story:

        story.entire_update(
            title=title,
            story_review=story_review,
            tag=tag,
            preview=preview,
            html_content=html_content,
            rep_pic=rep_pic
        )

        story.full_clean()
        story.save()

        return story

    def delete(self, story: Story):
        story.delete()


class StoryCommentCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, story_id: int, content: str, mentioned_email: str = '') -> StoryComment:
        story = Story.objects.get(id=story_id)

        comment_service = StoryCommentService()

        if mentioned_email:
            mentioned_user = User.objects.get(email=mentioned_email)
        else:
            mentioned_user = None

        story_comment = comment_service.create(
            story=story,
            content=content,
            mentioned_user=mentioned_user,
            writer=self.user
        )

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
        else:
            mentioned_user = None

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

    def create(self, story: Story, content: str, mentioned_user: User, writer: User) -> StoryComment:
        story_comment = StoryComment(
            story=story,
            content=content,
            mention=mentioned_user,
            writer=writer,
        )

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


class StoryMapService:
    def __init__(self):
        pass

    @staticmethod
    def create(story: Story):
        # 맵 사진 생성하기
        markers = []
        markers.append(Marker(
            longitude=story.place.longitude,
            latitude=story.place.latitude,
            label=story.place.place_name,
        ))

        file_path = 'map-for-story{}-{}.{}'.format(story.id,
                                                   str(time.time())+str(uuid.uuid4().hex), 'jpeg')
        map_image = ImageFile(io.BytesIO(
            get_static_naver_image(markers)), name=file_path)

        story_map = StoryMap(
            story=story,
            map=map_image
        )

        story_map.save()

    @ staticmethod
    def delete(story: Story):
        map = StoryMap.objects.get(story=story)
        map.delete()
