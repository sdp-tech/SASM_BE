import io
import time
import uuid
import datetime

from django.conf import settings
from django.db import transaction
from django.core.files.images import ImageFile
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile

from rest_framework import exceptions

from users.models import User
from places.models import Place, VisitorReview, VisitorReviewCategory, ReviewPhoto, CategoryContent


class PlaceService:
    def __init__(self):
        pass

    @transaction.atomic
    def like_or_dislike(user: User, place_id: int):

        place = Place.objects.get(id=place_id)

        check_like = user in place.place_likeuser_set.all()

        if check_like:
            place.place_likeuser_set.remove(user)
            place.place_like_cnt -= 1
            place.save()
            result = 'disliked'
        else:
            place.place_likeuser_set.add(user)
            place.place_like_cnt += 1
            place.save()
            result = 'liked'

        return result


class PlaceReviewCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, place: str, contents: str, photos: list[dict], category: list[dict]):
        post_review_service = PlaceReviewService()
        post_review = post_review_service.create(
            place_id=place,
            contents=contents,
            user=self.user
        )

        # 카테고리 개수만큼 create
        category_list = list(category.split(','))
       
        for i in range(len(category_list)):

            category_service = VisitorReviewCategoryService()
            category_service.create(
                category_id=category_list[i]
            )

        if len(photos) != 0:
            photo_service = ReviewPhotoService()
            photo_service.create(
                post_review=post_review,
                image_files=photos
            )


        return post_review


class PlaceReviewService:
    def __init__(self):
        pass

    @transaction.atomic
    def create(self, place_id: int, contents: str, user: str):
        place = Place.objects.get(id=place_id)
        post_review = VisitorReview(
            place=place,
            visitor_name=user,
            contents=contents
        )
        post_review.full_clean()
        post_review.save()

        return post_review


class ReviewPhotoService:
    def __init__(self):
        pass

    def create(self, post_review: VisitorReview, image_files: InMemoryUploadedFile ):

        place = VisitorReview.objects.select_related(
                    'place').filter(
                    id=post_review.id).values(
                    'place__place_name')
        place_name = place[0]['place__place_name']

        ext = image_files.name.split(".")[-1]
        file_path = '{}/{}/{}.{}'.format(place_name,post_review.id,str(datetime.datetime.now()),ext)
        image = ImageFile(io.BytesIO(image_files.read()), name=file_path)
 
        post_review_photo = ReviewPhoto(
            imgfile = image,
            review = post_review
        )

        post_review_photo.full_clean()
        post_review_photo.save()

        return post_review_photo


# TODO: handle category_choice(ManyToManyField)
class VisitorReviewCategoryService:
    def __init__(self):
        pass

    def create(self, category_id: str):
        category = CategoryContent.objects.get(id=category_id)
        post_review_category = VisitorReviewCategory(
            category=category
            # category_choice=post_review
        )

        post_review_category.full_clean()
        post_review_category.save()

        return post_review_category
