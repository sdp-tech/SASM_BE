import io
import time
import uuid

from django.conf import settings
from django.db import transaction
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import exceptions

from users.models import User
from community.models import Board, Post, PostHashtag, PostPhoto, PostComment, PostCommentPhoto, PostReport, PostCommentReport
from .selectors import BoardSelector, PostHashtagSelector, PostSelector, PostCommentSelector, PostCommentPhotoSelector


class PostCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, board_id: int, title: str, content: str, hashtag_names: list[str] = None, image_files: list[InMemoryUploadedFile] = None) -> Post:
        board = BoardSelector.get_from_id(id=board_id)

        post_service = PostService()
        post = post_service.create(
            title=title,
            content=content,
            board=board,
            writer=self.user
        )

        if hashtag_names:
            if not board.supports_hashtags:
                raise exceptions.ValidationError(
                    {"error": "해시태그를 지원하지 않는 게시판입니다."})
            hashtag_service = PostHashtagService(post=post)
            hashtag_service.create(names=hashtag_names)

        # [TODO] 문제점: tx가 중간에 실패할 경우, S3에 저장된 image는 삭제되지 않아 orphan 이미지 존재
        # 아래 링크처럼 예외 처리에서 boto3를 이용해 수동 삭제 or CRON을 이용해 주기적으로 orphan 정리
        # ref. https://stackoverflow.com/questions/50222974/django-transactions-how-to-run-extra-code-during-rollback
        if image_files:
            if not board.supports_post_photos:
                raise exceptions.ValidationError(
                    {"error": "게시글 사진을 지원하지 않는 게시판입니다."})
            photo_service = PostPhotoService(post=post)
            photo_service.create(image_files=image_files)

        return post

    @transaction.atomic
    def update(self, post_id: int, title: str, content: str, hashtag_names: list[str] = [], photo_image_urls: list[str] = [], image_files: list[InMemoryUploadedFile] = []) -> Post:
        post_service = PostService()
        post_selector = PostSelector()

        # user가 해당 post의 writer가 아닐 경우 에러 raise
        if not post_selector.isWriter(post_id=post_id, user=self.user):
            raise exceptions.ValidationError({"error": "게시글 작성자가 아닙니다."})

        post = post_service.update(
            post_id=post_id,
            title=title,
            content=content,
        )

        if post.board.supports_hashtags:
            hashtag_service = PostHashtagService(post=post)
            hashtag_service.update(names=hashtag_names)

        if post.board.supports_post_photos:
            photo_service = PostPhotoService(post=post)
            photo_service.update(
                photo_image_urls=photo_image_urls,
                image_files=image_files
            )

        return post

    @transaction.atomic
    def delete(self, post_id: int):
        post_service = PostService()
        post_selector = PostSelector()

        # user가 해당 post의 writer가 아닐 경우 에러 raise
        if not post_selector.isWriter(post_id=post_id, user=self.user):
            raise exceptions.ValidationError({"error": "게시글 작성자가 아닙니다."})

        # TODO: 더 이상 연결된 게시글이 없는 해시태그를 삭제해야될까?
        # 해시태그가 이후에 또 사용되거나, 대부분의 해시태그가 여러 게시글과 연결되어있는 것이 일반적이라 가정하면, 삭제하는 것은 불필요하다.
        # 향후에 orphan 해시태그가 너무 많아 성능에 문제가 생긴다면 orphan 해시태그 삭제 로직 추가를 고려해볼만하다.

        post_service.delete(post_id=post_id)

    @transaction.atomic
    def like_or_dislike(self, post_id: int) -> bool:
        user = self.user
        post = get_object_or_404(Post, pk=post_id)

        # 이미 좋아요 한 상태 -> 좋아요 취소 (dislike)
        if PostSelector.likes_post(user=user, post=post):
            PostService.dislike(user=user, post=post)
            return False
        else:  # 좋아요 하지 않은 상태 -> 좋아요 (like)
            PostService.like(user=user, post=post)
            return True


class PostService:
    def __init__(self):
        pass

    def create(self, title: str, content: str, board: Board, writer: User) -> Post:
        post = Post(
            title=title,
            content=content,
            board=board,
            writer=writer
        )

        post.full_clean()
        post.save()

        return post

    def update(self, post_id: int, title: str, content: str) -> Post:
        post = Post.objects.get(id=post_id)

        post.update_title(title)
        post.update_content(content)

        post.full_clean()
        post.save()

        return post

    def delete(self, post_id: int):
        post = Post.objects.get(id=post_id)

        post.delete()

    @staticmethod
    def like(user: User, post: Post):
        post.like(user=user)

        post.full_clean()
        post.save()

    @staticmethod
    def dislike(user: User, post: Post):
        post.dislike(user=user)

        post.full_clean()
        post.save()


class PostHashtagService:
    def __init__(self, post: Post):
        self.post = post

    def add_hashtag_to_post(self, name: str):
        # name을 가지는 해시태그가 존재하면 가져오고, 존재하지 않으면 생성
        if PostHashtagSelector.exists(name=name):
            hashtag = PostHashtag.objects.get(name=name)
        else:
            hashtag = PostHashtag(
                name=name
            )
            hashtag.full_clean()
            hashtag.save()

        hashtag.posts.add(self.post)

    def remove_hashtag_from_post(self, hashtag: PostHashtag):
        hashtag.posts.remove(self.post)

        # 더 이상 해시태그를 사용하는 게시글이 없으면 해시태그 삭제
        if not hashtag.posts.exists():
            hashtag.delete()

    def create(self, names: list[str]):
        # 중복된 이름을 가진 해시태그 제거를 위해 set 자료구조 사용
        names = set(names)

        for name in names:
            self.add_hashtag_to_post(name=name)

    def update(self, names: list[str]):
        # 중복된 이름을 가진 해시태그 제거를 위해 set 자료구조 사용
        names = set(names)

        current_hashtags = self.post.hashtags.all()

        # names에 포함되지 않은 해시태그 삭제
        for current_hashtag in current_hashtags:
            if current_hashtag.name not in names:
                self.remove_hashtag_from_post(current_hashtag)

        # 신규 name을 해시태그 생성
        for name in names:
            # 게시글에 이미 존재하는 해시태그면 스킵
            if PostSelector.has_hashtag(post=self.post, name=name):
                continue
            # 게시글에 존재하지 않는 해시태그면 추가
            self.add_hashtag_to_post(name=name)


class PostPhotoService:
    def __init__(self, post: Post):
        self.post = post

    def create(self, image_files: list[InMemoryUploadedFile]) -> PostPhoto:
        photos = []

        for image_file in image_files:
            ext = image_file.name.split(".")[-1]
            file_path = '{}-{}.{}'.format(self.post.id,
                                          str(time.time())+str(uuid.uuid4().hex), ext)
            image = ImageFile(io.BytesIO(image_file.read()), name=file_path)

            photo = PostPhoto(
                image=image,
                post=self.post
            )
            photo.full_clean()
            photo.save()

            photos.append(photo)

        return photos

    def update(self, photo_image_urls: list[str], image_files: list[InMemoryUploadedFile]):
        photos = []

        current_photos = self.post.photos.all()

        # photo_image_urls에 포함되지 않은 이미지를 가진 photo 삭제
        for current_photo in current_photos:
            image_path = settings.MEDIA_URL + str(current_photo.image)
            if image_path not in photo_image_urls:
                current_photo.delete()
            else:
                photos.append(current_photo)

        # 신규 image_file을 photo로 생성
        photos.extend(self.create(image_files=image_files))

        return photos


class PostCommentCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, post_id: int, isParent: bool, parent_id: int, content: str, mentioned_email: str, image_files: list[InMemoryUploadedFile] = None) -> PostComment:
        post = Post.objects.get(id=post_id)
        comment_selector = PostCommentSelector()
        comment_service = PostCommentService()

        # 해당 post가 속하는 board의 댓글 지원 여부 확인
        if not comment_selector.isPostCommentAvailable(post_id=post_id):
            raise exceptions.ValidationError({"error": "댓글을 지원하지 않는 게시글입니다."})

        if parent_id:
            parent = PostComment.objects.get(id=parent_id)
        else:
            parent = None

        if mentioned_email:
            mentioned_user = User.objects.get(email=mentioned_email)
        else:
            mentioned_user = None

        post_comment = comment_service.create(
            post=post,
            content=content,
            isParent=isParent,
            parent=parent,
            mentioned_user=mentioned_user,
            writer=self.user
        )

        photo_selector = PostCommentPhotoSelector()
        photo_service = PostCommentPhotoService(post_comment=post_comment)

        # 해당 post가 속하는 board의 댓글 사진 지원 여부 확인
        if image_files and not photo_selector.isPostCommentPhotoAvailable(post_id=post_id):
            raise exceptions.ValidationError(
                {"error": "댓글 사진을 지원하지 않는 게시글입니다."})

        photo_service.create(image_files=image_files)

        return post_comment

    @transaction.atomic
    def update(self, post_comment_id: int, content: str, mentioned_email: str, photo_image_urls: list[str] = [], image_files: list[InMemoryUploadedFile] = []) -> PostComment:
        post_comment_service = PostCommentService()
        post_comment_selector = PostCommentSelector()

        # user가 해당 post_comment의 writer가 아닐 경우 에러 raise
        if not post_comment_selector.isWriter(post_comment_id=post_comment_id, user=self.user):
            raise exceptions.ValidationError({"error": "댓글 작성자가 아닙니다."})

        if mentioned_email:
            mentioned_user = User.objects.get(email=mentioned_email)
        else:
            mentioned_user = None

        # elif mentioned_nickname:
        #     mention = User.objects.get(nickname=mentioned_nickname)

        post_comment = post_comment_service.update(
            post_comment_id=post_comment_id,
            content=content,
            mentioned_user=mentioned_user,
        )

        post_id = post_comment.post_id
        photo_selector = PostCommentPhotoSelector()
        photo_service = PostCommentPhotoService(post_comment=post_comment)

        # 해당 post가 속하는 board의 댓글 사진 지원 여부 확인
        if image_files and not photo_selector.isPostCommentPhotoAvailable(post_id=post_id):
            raise exceptions.ValidationError(
                {"error": "댓글 사진을 지원하지 않는 게시글입니다."})

        photo_service.update(
            photo_image_urls=photo_image_urls,
            image_files=image_files
        )

        return post_comment

    @transaction.atomic
    def delete(self, post_comment_id: int):
        post_comment_service = PostCommentService()
        post_comment_selector = PostCommentSelector()

        # user가 해당 post_comment의 writer가 아닐 경우 에러 raise
        if not post_comment_selector.isWriter(post_comment_id=post_comment_id, user=self.user):
            raise exceptions.ValidationError({"error": "댓글 작성자가 아닙니다."})

        post_comment_service.delete(post_comment_id=post_comment_id)


class PostCommentService:
    def __init__(self):
        pass

    def create(self, post: Post, content: str, isParent: bool, parent: PostComment, mentioned_user: User, writer: User) -> PostComment:
        post_comment = PostComment(
            post=post,
            content=content,
            isParent=isParent,
            parent=parent,
            mention=mentioned_user,
            writer=writer
        )

        post_comment.full_clean()
        post_comment.save()

        return post_comment

    def update(self, post_comment_id: int, content: str, mentioned_user: User) -> PostComment:
        post_comment = PostComment.objects.get(id=post_comment_id)

        post_comment.update_content(content)
        post_comment.update_mention(mentioned_user)

        post_comment.full_clean()
        post_comment.save()

        return post_comment

    def delete(self, post_comment_id: int):
        post_comment = PostComment.objects.get(id=post_comment_id)

        post_comment.delete()


class PostCommentPhotoService:
    def __init__(self, post_comment: PostComment):
        self.post_comment = post_comment

    def create(self, image_files: list[InMemoryUploadedFile]) -> PostCommentPhoto:
        photos = []

        for image_file in image_files:
            ext = image_file.name.split(".")[-1]
            file_path = '{}-{}.{}'.format(self.post_comment.id,
                                          str(time.time())+str(uuid.uuid4().hex), ext)
            image = ImageFile(io.BytesIO(image_file.read()), name=file_path)

            photo = PostCommentPhoto(
                image=image,
                post_comment=self.post_comment
            )

            photo.full_clean()
            photo.save()

            photos.append(photo)

        return photos

    def update(self, photo_image_urls: list[str], image_files: list[InMemoryUploadedFile]):
        photos = []

        current_photos = self.post_comment.photos.all()

        # photo_image_urls에 포함되지 않은 이미지를 가진 photo 삭제
        for current_photo in current_photos:
            image_path = settings.MEDIA_URL + str(current_photo.image)
            if image_path not in photo_image_urls:
                current_photo.delete()
            else:
                photos.append(current_photo)

        # 신규 image_file을 photo로 생성
        photos.extend(self.create(image_files=image_files))

        return photos


class PostReportService:
    def __init__(self):
        pass

    def create(self, post: int, category: str, reporter: User) -> PostReport:

        post_report = PostReport(
            post=post,
            category=category,
            reporter=reporter
        )

        post_report.full_clean()
        post_report.save()

        return post_report


class PostCommentReportService:
    def __init__(self):
        pass

    def create(self, post_comment: int, category: str, reporter: User) -> PostCommentReport:

        post_comment_report = PostCommentReport(
            comment=post_comment,
            category=category,
            reporter=reporter
        )

        post_comment_report.full_clean()
        post_comment_report.save()

        return post_comment_report
