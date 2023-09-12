import io
import time
import uuid

from django.conf import settings
from django.db import transaction
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import get_object_or_404

from users.models import User
from forest.models import Forest, ForestPhoto, ForestHashtag, Category, SemiCategory, ForestComment, ForestReport
from .selectors import ForestSelector, ForestCommentSelector
from core.exceptions import ApplicationError


class ForestCoordinatorService:
    def __init__(self):
        pass

    @staticmethod
    @transaction.atomic
    def create(title: str,
               subtitle: str,
               content: str,
               category: str,
               semi_categories: list[str],
               rep_pic: InMemoryUploadedFile,
               hashtags: list[str],
               photos: list[str],
               writer: User) -> Forest:

        forest = ForestService.create(
            title=title,
            subtitle=subtitle,
            content=content,
            category=category,
            semi_categories=semi_categories,
            rep_pic=rep_pic,
            writer=writer,
        )

        # 포레스트 게시글 이전에 생성된 ForestPhoto와 연결
        ForestPhotoService.process_photos(forest=forest,
                                          photos=photos)

        ForestHashtagService.process_hashtags(forest=forest,
                                              hashtags=hashtags)

        return forest

    @staticmethod
    @transaction.atomic
    def update(forest: Forest,
               title: str,
               subtitle: str,
               content: str,
               category: str,
               semi_categories: list[str],
               rep_pic: InMemoryUploadedFile,
               hashtags: list[str],
               photos: list[str]) -> Forest:

        forest = ForestService.update(
            forest=forest,
            title=title,
            subtitle=subtitle,
            content=content,
            category=category,
            semi_categories=semi_categories,
            rep_pic=rep_pic
        )

        # 연관 ForestPhoto와의 연결 업데이트
        ForestPhotoService.process_photos(forest=forest,
                                          photos=photos)

        ForestHashtagService.process_hashtags(forest=forest,
                                              hashtags=hashtags)

        return forest

    @staticmethod
    @transaction.atomic
    def delete(forest: Forest):
        forest.delete()


class ForestService:
    def __init__(self):
        pass

    @staticmethod
    def like_or_dislike(forest: Forest, user: User) -> bool:
        if ForestSelector.likes(forest=forest, user=user):
            forest.likeuser_set.remove(user)
            forest.like_cnt -= 1

            forest.full_clean()
            forest.save()

            return False
        else:
            forest.likeuser_set.add(user)
            forest.like_cnt += 1

            forest.full_clean()
            forest.save()

            return True

    @staticmethod
    def process_semi_categories(forest: Forest,
                                semi_categories: list[str]):
        for semi_category in semi_categories:
            op, semi_category_id = semi_category.split(',')
            semi_category = get_object_or_404(
                SemiCategory, id=semi_category_id)

            if op == 'add':
                semi_category.forest.add(forest)
            elif op == 'remove':
                semi_category.forest.remove(forest)
            else:
                raise ApplicationError("지원하지 않는 semi_category 연산입니다.")

        # forest의 현재 카테고리와 맞지않는 세미카테고리 제거 - 일관성 유지
        for semi_category in forest.semicategories.exclude(
                category=forest.category):
            semi_categories.remove(forest)

    @staticmethod
    def create(title: str,
               subtitle: str,
               content: str,
               category: str,
               semi_categories: list[str],
               rep_pic: InMemoryUploadedFile,
               writer: User) -> Forest:

        ext = rep_pic.name.split(".")[-1]
        file_path = '{}.{}'.format(str(time.time())+str(uuid.uuid4().hex), ext)
        rep_pic = ImageFile(io.BytesIO(rep_pic.read()), name=file_path)

        forest = Forest(
            title=title,
            subtitle=subtitle,
            content=content,
            category=get_object_or_404(Category, id=category),
            rep_pic=rep_pic,
            writer=writer
        )

        forest.full_clean()
        forest.save()

        ForestService.process_semi_categories(
            forest=forest,
            semi_categories=semi_categories
        )

        return forest

    @staticmethod
    def update(forest: Forest,
               title: str,
               subtitle: str,
               content: str,
               category: str,
               semi_categories: list[str],
               rep_pic: InMemoryUploadedFile) -> Forest:

        forest.title = title
        forest.subtitle = subtitle
        forest.content = content
        forest.category = get_object_or_404(Category, id=category)
        if rep_pic:
            ext = rep_pic.name.split(".")[-1]
            file_path = '{}.{}'.format(
                str(time.time())+str(uuid.uuid4().hex), ext)
            rep_pic = ImageFile(io.BytesIO(rep_pic.read()), name=file_path)
            forest.rep_pic = rep_pic

        forest.full_clean()
        forest.save()

        ForestService.process_semi_categories(
            forest=forest,
            semi_categories=semi_categories
        )

        return forest

    @staticmethod
    def report(forest: Forest,
               report_category: str,
               reporter: User):

        forest_report = ForestReport(
            forest=forest,
            category=report_category,
            reporter=reporter
        )

        forest_report.full_clean()
        forest_report.save()


class ForestPhotoService:
    def __init__(self):
        pass

    @staticmethod
    def create(image: InMemoryUploadedFile):
        ext = image.name.split(".")[-1]
        file_path = '{}.{}'.format(str(time.time())+str(uuid.uuid4().hex), ext)
        image = ImageFile(io.BytesIO(image.read()), name=file_path)
        photo = ForestPhoto(image=image, forest=None)

        photo.full_clean()
        photo.save()

        return settings.MEDIA_URL + photo.image.name

    @staticmethod
    def process_photos(forest: Forest, photos: list[str]):
        for photo in photos:
            op, photo_url = photo.split(',')
            photo = get_object_or_404(
                ForestPhoto, image=photo_url.replace(settings.MEDIA_URL, ''))

            if op == 'add':
                photo.forest = forest
                photo.full_clean()
                photo.save()
            elif op == 'remove':
                photo.delete()
            else:
                raise ApplicationError("지원하지 않는 photo 연산입니다.")


class ForestHashtagService:
    def __init__(self):
        pass

    @staticmethod
    def process_hashtags(forest: Forest, hashtags: list[str]):
        for hashtag in hashtags:
            op, name = hashtag.split(',')
            hashtag = ForestHashtag.objects.filter(forest=forest, name=name)

            if op == 'add' and not hashtag.exists():
                hashtag = ForestHashtag(forest=forest, name=name)
                hashtag.full_clean()
                hashtag.save()
            elif op == 'remove' and hashtag.exists():
                # {forest, name}이 pk이므로 object는 unique하게 존재함이 보장
                hashtag[0].delete()
            else:
                raise ApplicationError("지원하지 않는 hashtag 연산입니다.")


class ForestCommentService:
    def __init__(self):
        pass

    @staticmethod
    def create(forest: Forest, content: str, writer: User) -> ForestComment:
        forest_comment = ForestComment(
            forest=forest,
            content=content,
            writer=writer
        )

        forest_comment.full_clean()
        forest_comment.save()

        return forest_comment

    @staticmethod
    def update(forest_comment: ForestComment, content: str) -> ForestComment:
        forest_comment.content = content

        forest_comment.full_clean()
        forest_comment.save()

        return forest_comment

    @staticmethod
    def delete(forest_comment: ForestComment):
        forest_comment.delete()

    @staticmethod
    def like_or_dislike(forest_comment: ForestComment, user: User) -> bool:
        if ForestCommentSelector.likes(forest_comment=forest_comment, user=user):
            forest_comment.likeuser_set.remove(user)
            forest_comment.like_cnt -= 1

            forest_comment.full_clean()
            forest_comment.save()

            return False
        else:
            forest_comment.likeuser_set.add(user)
            forest_comment.like_cnt += 1

            forest_comment.full_clean()
            forest_comment.save()

            return True

class ForestUserCategoryService:
    def __init__(self, user: User):
        self.user = user

    def save_usercategory(self, semi_categories:list[str]) -> User:

        self.user.semi_categories.clear()
        
        if semi_categories:
            for category_id_str in semi_categories:
                try:
                    category_id = int(category_id_str)
                    # 'semi_categories'가 many-to-many 필드인 경우, 각 ID를 연결하기 위해 'add'를 사용
                    self.user.semi_categories.add(category_id)
                except ValueError:
                    # 유효하지 않은 ID를 무시하거나 로깅할 수 있습니다.
                    pass

        self.user.save()

        return self.user