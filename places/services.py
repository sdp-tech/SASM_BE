import io
import time
import uuid
import datetime

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction
from django.core.files.images import ImageFile
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile

from rest_framework import exceptions

from users.models import User
from places.models import Place, PlaceVisitorReview, PlaceVisitorReviewCategory, PlaceVisitorReviewPhoto, CategoryContent, SNSUrl, PlacePhoto, SNSType
from places.selectors import PlaceReviewSelector
from places.views.save_place_excel import addr_to_lat_lon

class PlaceDetailService:
    @staticmethod
    def get_place_detail(place_id):
        try:
            place = Place.objects.select_related('story').get(id=place_id)
            return place
        except Place.DoesNotExist:
            raise Place.DoesNotExist("장소를 찾을 수 없습니다.")

class PlaceCoordinatorService:
    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def create(place_name: str, category: str, vegan_category: str, tumblur_category: bool,
               reusable_con_category: bool, pet_category: bool, mon_hours: str, tues_hours: str,
               wed_hours: str, thurs_hours: str, fri_hours: str, sat_hours: str, sun_hours: str,
               etc_hours: str, place_review: str, address: str, short_cur: str, phone_num: str,
               rep_pic: InMemoryUploadedFile, imageList: list[InMemoryUploadedFile], snsList: list[str]) -> Place:

        place = PlaceService.create(place_name=place_name, category=category, vegan_category=vegan_category,
                                    tumblur_category=tumblur_category, reusable_con_category=reusable_con_category,
                                    pet_category=pet_category, mon_hours=mon_hours, tues_hours=tues_hours,
                                    wed_hours=wed_hours, thurs_hours=thurs_hours, fri_hours=fri_hours, sat_hours=sat_hours,
                                    sun_hours=sun_hours, etc_hours=etc_hours, address=address, place_review=place_review,
                                    short_cur=short_cur,  rep_pic=rep_pic, phone_num=phone_num)

        PlacePhotoService.create(place=place, imageList=imageList)
        PlaceSNSUrlService.create(place=place, snsList=snsList)

        return place
    
    def update_place(self, place_id, update_data):
        try:
            place = Place.objects.get(id=place_id)
        except Place.DoesNotExist:
            raise Place.DoesNotExist("장소를 찾을 수 없습니다.")

        for field, value in update_data.items():
            setattr(place, field, value)

        place.save()

        if 'imageList' in update_data:
            PlacePhotoService.update_place_photos(place, update_data['imageList'])

        if 'snsList' in update_data:
            PlaceSNSUrlService.update_place_sns_urls(place, update_data['snsList'])

class PlaceService:
    def __init__(self):
        pass

    @staticmethod
    def create(place_name: str, category: str, vegan_category: str, tumblur_category: bool,
               reusable_con_category: bool, pet_category: bool, mon_hours: str, tues_hours: str,
               wed_hours: str, thurs_hours: str, fri_hours: str, sat_hours: str, sun_hours: str,
               etc_hours: str, place_review: str, address: str, short_cur: str, rep_pic: InMemoryUploadedFile,
               phone_num: str) -> Place:

        longitude, latitude = addr_to_lat_lon(address)

        place = Place(
            place_name=place_name,
            category=category,
            vegan_category=vegan_category,
            tumblur_category=tumblur_category,
            reusable_con_category=reusable_con_category,
            pet_category=pet_category,
            mon_hours=mon_hours,
            tues_hours=tues_hours,
            wed_hours=wed_hours,
            thurs_hours=thurs_hours,
            fri_hours=fri_hours,
            sat_hours=sat_hours,
            sun_hours=sun_hours,
            etc_hours=etc_hours,
            place_review=place_review,
            address=address,
            short_cur=short_cur,
            latitude=latitude,
            longitude=longitude,
            rep_pic=rep_pic,
            phone_num=phone_num,
            is_released=False,  # 심사 중인 상태로 설정
        )

        place.full_clean()
        place.save()

        return place


class PlacePhotoService:
    def __init__(self):
        pass

    @staticmethod
    def create(place: Place, imageList: list[InMemoryUploadedFile]) -> PlacePhoto:
        for image_file in imageList:
            ext = image_file.name.split(".")[-1]
            file_path = '{}-{}.{}'.format(place.id,
                                          str(time.time())+str(uuid.uuid4().hex), ext)
            image = ImageFile(io.BytesIO(image_file.read()), name=file_path)

            photo = PlacePhoto(
                image=image,
                place=place
            )
            photo.full_clean()
            photo.save()

    def get_place_photos(place: Place):
        return [photo.image.url for photo in place.photos.all()]
    
    def update_place_photos(place: Place, imageList: list[InMemoryUploadedFile]):
        existing_photos = place.photos.all()
        existing_urls = set(photo.image.url for photo in existing_photos)

        for image_file in imageList:
            ext = image_file.name.split(".")[-1]
            file_path = '{}-{}.{}'.format(place.id, str(time.time())+str(uuid.uuid4().hex), ext)
            image = ImageFile(image_file, name=file_path)

            if image.url not in existing_urls:
                photo = PlacePhoto(image=image, place=place)
                photo.full_clean()
                photo.save()

class PlaceSNSUrlService:
    def __init__(self):
        pass

    @staticmethod
    def create(place: Place, snsList: list[str]) -> SNSUrl:
        for sns_pair in snsList:
            sns_type, url = sns_pair.split(',')
            sns_url = SNSUrl(
                place=place,
                snstype=get_object_or_404(SNSType, pk=sns_type),
                url=url,
            )

            sns_url.full_clean()
            sns_url.save()

    def get_place_sns_urls(place: Place):
        sns_list = []
        for sns in place.place_sns_url.all():
            sns_list.append({
                'sns_type': sns.snstype.id,
                'url': sns.url
            })
        return sns_list
    
    def update_place_sns_urls(place: Place, snsList: list[str]):
        existing_sns_urls = [sns.url for sns in place.place_sns_url.all()]

        for sns_pair in snsList:
            sns_type, url = sns_pair.split(',')

            if url not in existing_sns_urls:
                sns_url = SNSUrl(
                    place=place,
                    snstype=get_object_or_404(SNSType, pk=sns_type),
                    url=url,
                )

                sns_url.full_clean()
                sns_url.save()

class PlaceVisitorReviewCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, place_id: str, contents: str, images: list[InMemoryUploadedFile], category: str) -> PlaceVisitorReview:
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

        if len(images) > 0:
            photo_service = PlaceVisitorReviewPhotoService(
                place_review=place_review)
            photo_service.create(
                place_review=place_review,
                image_files=images
            )

        return place_review

    @transaction.atomic
    def update(self, place_review_id: int, category: str, contents: str, photo_image_urls: list[str] = [], image_files: list[InMemoryUploadedFile] = []) -> PlaceVisitorReview:
        place_review = PlaceVisitorReview.objects.get(id=place_review_id)
        place_review_service = PlaceVisitorReviewService()
        place_review_selector = PlaceReviewSelector()

        if not place_review_selector.isWriter(place_review_id=place_review_id, user=self.user):
            raise exceptions.ValidationError({"detail": "리뷰 작성자가 아닙니다."})

        place_review = place_review_service.update(
            place_review_id=place_review_id,
            contents=contents,
        )

        photo_service = PlaceVisitorReviewPhotoService(
            place_review=place_review)
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
        photos = []

        for image_file in image_files:

            ext = image_file.name.split(".")[-1]
            file_path = '{}/{}-{}.{}'.format(place_review.id, place_review.id,
                                             str(time.time())+str(uuid.uuid4().hex), ext)
            image = ImageFile(io.BytesIO(image_file.read()), name=file_path)

            place_review_photo = PlaceVisitorReviewPhoto(
                imgfile=image,
                review=place_review
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
            place_review_category = PlaceVisitorReviewCategory(
                category=category)

            place_review_category.full_clean()
            place_review_category.save()
            place_review_category.category_choice.add(category_choice)

        categories = PlaceVisitorReviewCategory.objects.filter(
            category_choice=category_choice)

        return categories

    @transaction.atomic
    def update(self, category_list: list[str], category_choice: PlaceVisitorReview):

        current_categories = PlaceVisitorReviewCategory.objects.filter(
            category_choice=category_choice)

        for category in current_categories:
            if str(category.category.id) not in category_list:
                category.delete()
            else:
                # 이미 존재하는 카테고리 데이터는 새로 생성하지 않음
                category_list.remove(str(category.category.id))

        self.create(category_list=category_list,
                    category_choice=category_choice)
        updated_category = PlaceVisitorReviewCategory.objects.filter(
            category_choice=category_choice)

        return updated_category
