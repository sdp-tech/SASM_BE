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


class PlaceReviewCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, place_id: str, contents: str, photos: InMemoryUploadedFile = None, category: str = None):
        place_review_service = PlaceReviewService()
        place_review = place_review_service.create(
            place_id=place_id,
            contents=contents,
            user=self.user
        )

        # 카테고리 개수만큼 create, FE에서 최대 3개 선택 제한
        if category != None:
            category_list = list(category.split(','))
            for idx in range(len(category_list)):

                category_service = PlaceReviewCategoryService()
                category_service.create(
                    category_id=category_list[idx],
                    category_choice=place_review
                )

        if photos != None:
            photo_service = PlaceReviewPhotoService()
            photo_service.create(
                place_review=place_review,
                image_files=photos
            )
        
        return place_review


class PlaceReviewService:
    def __init__(self):
        pass

    @transaction.atomic
    def create(self, place_id: int, contents: str, user: str):
        place = Place.objects.get(id=place_id)
        place_review = VisitorReview(
            place=place,
            visitor_name=user,
            contents=contents
        )
        place_review.full_clean()
        place_review.save()

        return place_review


class PlaceReviewPhotoService:
    def __init__(self):
        pass

    def create(self, place_review: VisitorReview, image_files: InMemoryUploadedFile):

        place_name = VisitorReview.objects.get(id=place_review.id).place.place_name

        ext = image_files.name.split(".")[-1]
        file_path = '{}/{}-{}.{}'.format(place_name, place_review.id,
                                        str(time.time())+str(uuid.uuid4().hex), ext)
        image = ImageFile(io.BytesIO(image_files.read()), name=file_path)

        place_review_photo = ReviewPhoto(
            imgfile = image,
            review = place_review
        )

        place_review_photo.full_clean()
        place_review_photo.save()

        return place_review_photo


class PlaceReviewCategoryService:
    def __init__(self):
        pass

    def create(self, category_id: str, category_choice: VisitorReview):
        category = CategoryContent.objects.get(id=category_id)
        place_review_category = VisitorReviewCategory(category=category)

        place_review_category.full_clean()
        place_review_category.save()
        place_review_category.category_choice.add(category_choice)

        return place_review_category