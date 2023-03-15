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
from places.models import Place, PlaceVisitorReview, PlaceVisitorReviewCategory, PlaceVisitorReviewPhoto, CategoryContent
from places.selectors import PlaceReviewSelector

class PlaceVisitorReviewCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, place_id: str, contents: str, photos: list[InMemoryUploadedFile], category: str) -> PlaceVisitorReview:
        place_review_service = PlaceVisitorReviewService()
        place_review = place_review_service.create(
            place_id=place_id,
            contents=contents,
            user=self.user
        )

        # 카테고리 개수만큼 create, FE에서 최대 3개 선택 제한
        if category != '':
            category_list = list(category.split(','))
            category_service = PlaceVisitorReviewCategoryService()
            category_service.create(
                category_list=category_list,
                category_choice=place_review
            )
            
        if len(photos) > 0:
            photo_service = PlaceVisitorReviewPhotoService(place_review=place_review)
            photo_service.create(
                place_review=place_review,
                image_files=photos
            )
        
        return place_review
    
    @transaction.atomic
    def update(self, place_review_id: int, category: str, contents: str, photo_image_urls: list[str] = [], image_files: list[InMemoryUploadedFile] = []) -> PlaceVisitorReview:
        place_review = PlaceVisitorReview.objects.get(id=place_review_id)
        place_review_service = PlaceVisitorReviewService()
        place_review_selector = PlaceReviewSelector()

        if not place_review_selector.isWriter(place_review_id=place_review_id, user=self.user):
            raise exceptions.ValidationError({"error": "리뷰 작성자가 아닙니다."})

        place_review = place_review_service.update(
            place_review_id=place_review_id,
            contents=contents,
        )

        photo_service = PlaceVisitorReviewPhotoService(place_review=place_review)
        photo_service.update(
            place_review=place_review,
            photo_image_urls=photo_image_urls,
            image_files=image_files,
        )
        
        if category != '':
            category_list = list(category.split(','))

            category_service = PlaceVisitorReviewCategoryService()
            category_service.update(
                category_list=category_list,
                category_choice=place_review
            )


class PlaceVisitorReviewService:
    def __init__(self):
        pass

    @transaction.atomic
    def create(self, place_id: int, contents: str, user: str):
        place = Place.objects.get(id=place_id)
        place_review = PlaceVisitorReview(
            place=place,
            visitor_name=user,
            contents=contents
        )
        place_review.full_clean()
        place_review.save()

        return place_review

    @transaction.atomic
    def update(self, place_review_id: int, contents: str) -> PlaceVisitorReview:
        place_review = PlaceVisitorReview.objects.get(id=place_review_id)
        
        place_review.update_contents(contents)

        place_review.full_clean()
        place_review.save()

        return place_review


class PlaceVisitorReviewPhotoService:
    def __init__(self, place_review: PlaceVisitorReview):
        self.place_review = place_review

    @transaction.atomic
    def create(self, place_review: PlaceVisitorReview, image_files: list[InMemoryUploadedFile]):
        place_name = PlaceVisitorReview.objects.get(id=place_review.id).place.place_name
        photos = []

        for image_file in image_files:

            ext = image_file.name.split(".")[-1]
            file_path = '{}/{}-{}.{}'.format(place_name, place_review.id,
                                            str(time.time())+str(uuid.uuid4().hex), ext)
            image = ImageFile(io.BytesIO(image_file.read()), name=file_path)

            place_review_photo = PlaceVisitorReviewPhoto(
                imgfile = image,
                review = place_review
            )

            place_review_photo.full_clean()
            place_review_photo.save()

            photos.append(place_review_photo)

        return photos

    @transaction.atomic
    def update(self, place_review: PlaceVisitorReview, photo_image_urls: list[str], image_files: list[InMemoryUploadedFile]):
        photos = []

        current_photos = self.place_review.photos.all()

        for current_photo in current_photos:
            image_path = settings.MEDIA_URL + str(current_photo.imgfile)
            if image_path not in photo_image_urls:
                current_photo.delete()
            else:
                photos.append(current_photo)

        self.create(place_review=place_review, image_files=image_files)

        updated_photos = self.place_review.photos.all()
        photos.extend(updated_photos)

        return photos


class PlaceVisitorReviewCategoryService:
    def __init__(self):
        pass

    @transaction.atomic
    def create(self, category_list: list[str], category_choice: PlaceVisitorReview):

        for category in category_list:

            category = CategoryContent.objects.get(id=category)
            place_review_category = PlaceVisitorReviewCategory(category=category)

            place_review_category.full_clean()
            place_review_category.save()
            place_review_category.category_choice.add(category_choice)

        categories = PlaceVisitorReviewCategory.objects.filter(category_choice=category_choice)

        return categories

    @transaction.atomic
    def update(self, category_list: list[str], category_choice: PlaceVisitorReview):

        current_categories = PlaceVisitorReviewCategory.objects.filter(category_choice=category_choice)

        for category in current_categories:
            if str(category.category.id) not in category_list:
                category.delete()
            else:
                category_list.remove(str(category.category.id)) # 이미 존재하는 카테고리 데이터는 새로 생성하지 않음

        self.create(category_list=category_list, category_choice=category_choice)
        updated_category = PlaceVisitorReviewCategory.objects.filter(category_choice=category_choice)

        return updated_category