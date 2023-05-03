import io
import time
import uuid
import json

from django.conf import settings
from django.db import transaction
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile

from rest_framework import exceptions

from users.models import User
from community.models import Board, Post, PostHashtag, PostPhoto, PostLike, PostComment, PostCommentPhoto, PostReport, PostCommentReport, PostPlace
from .selectors import BoardSelector, PostHashtagSelector, PostSelector, PostLikeSelector, PostCommentSelector, PostCommentPhotoSelector
from core.exceptions import ApplicationError


class PostCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, board_id: int, title: str, content: str, hashtag_names: list[str] = [], image_files: list[InMemoryUploadedFile] = [],
               subtitle: str = '', keyword: str = '', places: list[str] = []) -> Post:
        board = BoardSelector.get_from_id(id=board_id)

        post_service = PostService()
        post = post_service.create(
            title=title,
            content=content,
            board=board,
            writer=self.user,
            subtitle=subtitle,
            keyword=keyword,
        )

        if board.supports_hashtags and hashtag_names:
            hashtag_service = PostHashtagService(post=post)
            hashtag_service.create(names=hashtag_names)

        # [TODO] 문제점: tx가 중간에 실패할 경우, S3에 저장된 image는 삭제되지 않아 orphan 이미지 존재
        # 아래 링크처럼 예외 처리에서 boto3를 이용해 수동 삭제 or CRON을 이용해 주기적으로 orphan 정리
        # ref. https://stackoverflow.com/questions/50222974/django-transactions-how-to-run-extra-code-during-rollback
        if board.supports_post_photos and image_files:
            photo_service = PostPhotoService(post=post)
            photo_service.create(image_files=image_files)

        if places:
            PostPlaceService.create(post=post, place_jsons=places)

        return post

    @transaction.atomic
    def update(self, post: Post, title: str, content: str, hashtag_names: list[str] = [], photo_image_urls: list[str] = [], image_files: list[InMemoryUploadedFile] = [],
               subtitle: str = '', keyword: str = '', places: list[str] = []) -> Post:
        post_service = PostService()
        post_selector = PostSelector()

        post = post_service.update(
            post=post,
            title=title,
            content=content,
            subtitle=subtitle,
            keyword=keyword,
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

        if places:
            PostPlaceService.update(post=post, place_jsons=places)

        return post

    @transaction.atomic
    def delete(self, post: Post):
        post_service = PostService()
        post_service.delete(post=post)

    @transaction.atomic
    def like_or_dislike(self, post: Post) -> bool:
        # 이미 좋아요 한 상태 -> 좋아요 취소 (dislike)
        if PostLikeSelector.likes(post_id=post.id, user=self.user):
            # PostLike 삭제
            PostLikeService.dislike(
                post_id=post.id,
                user=self.user
            )

            # Post의 like_cnt 1 감소
            PostService.dislike(post_id=post.id)
            return False

        else:  # 좋아요 하지 않은 상태 -> 좋아요 (like)
            # PostLike 생성
            PostLikeService.like(
                post_id=post.id,
                user=self.user
            )

            # Post의 like_cnt 1 증가
            PostService.like(post_id=post.id)
            return True


class PostService:
    def __init__(self):
        pass

    def create(self, title: str, content: str, board: Board, writer: User, subtitle: str, keyword: str) -> Post:
        post = Post(
            title=title,
            content=content,
            board=board,
            writer=writer,
            subtitle=subtitle,
            keyword=keyword,
        )

        post.full_clean()
        post.save()

        return post

    def update(self, post: Post, title: str, content: str, subtitle: str, keyword: str) -> Post:
        post.entire_update(
            title=title,
            content=content,
            subtitle=subtitle,
            keyword=keyword,
        )

        post.full_clean()
        post.save()

        return post

    def delete(self, post: Post):
        post.delete()

    @staticmethod
    def like(post_id: int):
        post = Post.objects.get(id=post_id)

        post.like()

        post.full_clean()
        post.save()

    @staticmethod
    def dislike(post_id: int):
        post = Post.objects.get(id=post_id)

        post.dislike()

        post.full_clean()
        post.save()


class PostHashtagService:
    def __init__(self, post: Post):
        self.post = post

    def create(self, names: list[str]):
        hashtags = []

        # 중복된 이름을 가진 해시태그 제거를 위해 set 자료구조 사용
        names = set(names)

        for name in names:
            hashtag = PostHashtag(
                name=name,
                post=self.post
            )

            hashtag.full_clean()
            hashtag.save()

            hashtags.append(hashtag)

        return hashtags

    def update(self, names: list[str]):
        hashtags = []

        current_hashtags = self.post.hashtags.all()

        # names에 포함되지 않은 해시태그 삭제
        for current_hashtag in current_hashtags:
            if current_hashtag.name not in names:
                current_hashtag.delete()
            else:
                hashtags.append(current_hashtag)

        # 신규 name을 해시태그 생성
        selector = PostHashtagSelector()
        for name in names:
            # 이미 존재하는 해시태그면 스킵
            if selector.exists(post=self.post, name=name):
                continue
            # 존재하지 않으면 생성
            hashtag = PostHashtag(
                name=name,
                post=self.post
            )
            hashtag.full_clean()
            hashtag.save()

            hashtags.append(hashtag)

        return hashtags


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


class PostLikeService:
    def __init__(self):
        pass

    @staticmethod
    def like(post_id: int, user: User):
        like = PostLike(
            post=Post.objects.get(id=post_id),
            user=user
        )
        like.full_clean()
        like.save()

    @staticmethod
    def dislike(post_id: int, user: User):
        PostLike.objects.get(post__id=post_id, user=user).delete()


class PostPlaceService:
    def __init__(self):
        pass

    @staticmethod
    def create(post: Post, place_jsons: list[str]):
        for place_json in place_jsons:
            place_dict = json.loads(place_json)
            post_place = PostPlace(
                post=post,
                ** place_dict,
            )

            post_place.full_clean()
            post_place.save()

    @staticmethod
    def update(post: Post, place_jsons: list[str]):
        current_places = post.places.all()
        places = [json.loads(place_json) for place_json in place_jsons]
        current_place_dicts = []

        # place_jsons에 포함되지 않는 장소 삭제
        for current_place in current_places:
            current_place_dict = {
                'name': current_place.name,
                'address': current_place.address,
                'contact': current_place.contact,
                'latitude': current_place.latitude,
                'longitude': current_place.longitude}
            current_place_dicts.append(current_place_dict)
            if current_place_dict not in places:
                current_place.delete()

        # 새롭게 전달된 장소 생성
        new_place_jsons = []
        for place in places:
            if place not in current_place_dicts:
                new_place_jsons.append(json.dumps(place))
        PostPlaceService.create(
            post=post,
            place_jsons=new_place_jsons
        )


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
            raise ApplicationError("댓글을 지원하지 않는 게시글입니다.")

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
            raise ApplicationError("댓글 사진을 지원하지 않는 게시글입니다.")

        photo_service.create(image_files=image_files)

        return post_comment

    @transaction.atomic
    def update(self, post_comment: PostComment, content: str, mentioned_email: str, photo_image_urls: list[str] = [], image_files: list[InMemoryUploadedFile] = []) -> PostComment:
        post_comment_service = PostCommentService()

        if mentioned_email:
            mentioned_user = User.objects.get(email=mentioned_email)
        else:
            mentioned_user = None

        # elif mentioned_nickname:
        #     mention = User.objects.get(nickname=mentioned_nickname)

        post_comment = post_comment_service.update(
            post_comment=post_comment,
            content=content,
            mentioned_user=mentioned_user,
        )

        post_id = post_comment.post_id
        photo_selector = PostCommentPhotoSelector()
        photo_service = PostCommentPhotoService(post_comment=post_comment)

        # 해당 post가 속하는 board의 댓글 사진 지원 여부 확인
        if image_files and not photo_selector.isPostCommentPhotoAvailable(post_id=post_id):
            raise ApplicationError("댓글 사진을 지원하지 않는 게시글입니다.")

        photo_service.update(
            photo_image_urls=photo_image_urls,
            image_files=image_files
        )

        return post_comment

    @transaction.atomic
    def delete(self, post_comment: PostComment):
        post_comment_service = PostCommentService()
        post_comment_service.delete(post_comment=post_comment)


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

    def update(self, post_comment: PostComment, content: str, mentioned_user: User) -> PostComment:
        post_comment.update_content(content)
        post_comment.update_mention(mentioned_user)

        post_comment.full_clean()
        post_comment.save()

        return post_comment

    def delete(self, post_comment: PostComment):
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
