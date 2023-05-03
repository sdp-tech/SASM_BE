import io
import time
import uuid

from django.conf import settings
from django.db import transaction
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import InMemoryUploadedFile

from users.models import User
from stories.models import Story
from places.models import PlacePhoto
from curations.models import Curation, Curation_Story, CurationPhoto, CurationMap
from curations.selectors import CurationLikeSelector
from core.map_image import Marker, get_static_naver_image


class CurationCoordinatorService:
    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def create(self, title: str, stories: list, short_curations: list, contents: str, rep_pic: InMemoryUploadedFile, is_released: bool, is_selected: bool, is_rep: bool):

        curation_service = CurationService()
        curation = curation_service.create(
            title=title,
            contents=contents,
            writer=self.user,
            is_released=is_released,  # 개발용
            is_selected=is_selected,  # 개발용
            is_rep=is_rep  # 개발용
        )

        short_curation_service = ShortCurationService()
        stories_qs = Story.objects.filter(id__in=stories)
        short_curations = short_curation_service.create(
            curation=curation,
            stories=stories_qs,
            short_curations=short_curations
        )

        photo_service = CurationPhotoService()
        photo_service.create(curation=curation, image_file=rep_pic)

        CurationMapService.create(curation=curation, stories=stories_qs)

        return curation

    @transaction.atomic
    def update(self, curation: Curation, title: str, stories: list[str], short_curations: list, contents: str, photo_image_url: str, rep_pic: InMemoryUploadedFile):

        curation_service = CurationService()
        curation = curation_service.update(
            curation=curation,
            title=title,
            contents=contents
        )

        pairs = {}  # {[<Story: 스토리4>]>: '숏큐 내용'}
        stories_qs = Story.objects.filter(id__in=stories)  # obj list

        for i, story in enumerate(stories_qs):
            pairs[story] = short_curations[i]

        short_curation_service = ShortCurationService()
        short_curations = short_curation_service.update(
            curation=curation,
            pairs=pairs,
            stories=stories_qs
        )

        if rep_pic:
            photo_service = CurationPhotoService()
            photo_service.update(
                curation=curation, photo_image_url=photo_image_url, image_file=rep_pic)

        CurationMapService.delete(curation=curation)
        CurationMapService.create(curation=curation, stories=stories_qs)

        return curation

    @transaction.atomic
    def delete(self, curation: Curation):
        curation_service = CurationService()
        curation_service.delete(curation=curation)


class ShortCurationService:
    def __init__(self):
        pass

    @transaction.atomic
    def create(self, curation: Curation, stories: list[Story], short_curations: list[str]):

        for i in range(len(stories)):
            short_curation = Curation_Story(
                curation=curation,
                story=stories[i],
                short_curation=short_curations[i]
            )
            short_curation.full_clean()
            short_curation.save()

        return short_curations

    @transaction.atomic
    def update(self, curation: Curation, pairs: dict, stories: list[Story]):

        pairs_to_create = pairs.copy()
        current_objs = curation.short_curations.all()  # Story-Curation objs

        for obj in current_objs:
            story = obj.story
            sc = obj.short_curation

            # 선택 취소된 스토리(Story_Curation obj) 삭제
            if story not in stories:
                obj.delete()

            # 스토리에 대한 숏큐 내용 변경
            elif sc != pairs[story]:
                obj.update_short_curation(short_curation=pairs[story])
                obj.full_clean()
                obj.save()
                del pairs_to_create[story]

            # 내용 일치
            else:
                del pairs_to_create[story]

        # 새로 생성
        sc_qs = Curation_Story.objects.none()
        story_qs = Story.objects.none()
        sc_list = []

        if len(pairs_to_create) > 0:
            for story in pairs_to_create:
                story_qs |= Story.objects.filter(id=story.id)
                sc_list.append(pairs_to_create[story])

            sc_qs |= self.create(curation=curation,
                                 stories=story_qs,
                                 short_curations=sc_list)

        return sc_qs


class CurationService:
    def __init__(self):
        pass

    def create(self, title: str, contents: str, writer: User, is_released: bool, is_selected: bool, is_rep: bool):
        curation = Curation(
            title=title,
            contents=contents,
            writer=writer,
            is_released=is_released,  # 개발용
            is_selected=is_selected,  # 개발용
            is_rep=is_rep  # 개발용
        )

        curation.full_clean()
        curation.save()

        return curation

    def update(self, curation: Curation, title: str, contents: str):
        curation.update_title(title)
        curation.update_contents(contents)

        curation.full_clean()
        curation.save()

        return curation

    def delete(self, curation: Curation):
        curation.delete()


class CurationPhotoService:
    def __init__(self):
        pass

    def create(self, curation: Curation, image_file: InMemoryUploadedFile):
        ext = image_file.name.split(".")[-1]
        file_path = '{}-{}.{}'.format(curation.id,
                                      str(time.time())+str(uuid.uuid4().hex), ext)
        image = ImageFile(io.BytesIO(image_file.read()), name=file_path)

        rep_pic = CurationPhoto(
            image=image,
            curation=curation
        )
        rep_pic.full_clean()
        rep_pic.save()

        return rep_pic

    def update(self, curation: Curation, photo_image_url: str, image_file: InMemoryUploadedFile):
        current_rep_pic = curation.photos.all()  # queryset 형태
        image_path = settings.MEDIA_URL + str(current_rep_pic[0].image)

        if image_path != photo_image_url:
            current_rep_pic.delete()
            rep_pic = self.create(curation=curation, image_file=image_file)
        else:
            rep_pic = current_rep_pic

        return rep_pic


class CurationLikeService:
    def __init__(self):
        pass

    @staticmethod
    def like(curation: Curation, user: User):
        curation.likeuser_set.add(user)

    @staticmethod
    def dislike(curation: Curation, user: User):
        curation.likeuser_set.remove(user)

    @staticmethod
    def like_or_dislike(curation: Curation, user: User):
        likes = CurationLikeSelector.likes(curation=curation, user=user)
        if not likes:
            CurationLikeService.like(curation=curation, user=user)
            return True
        else:
            CurationLikeService.dislike(curation=curation, user=user)
            return False


class CurationMapService:
    def __init__(self):
        pass

    @staticmethod
    def create(curation: Curation, stories: list[Story]):
        places = list(map(lambda x: x.address, stories))

        # 사진 생성하기
        markers = []
        for place in places:
            markers.append(Marker(
                longitude=place.longitude,
                latitude=place.latitude,
                label=place.place_name,
            ))

        file_path = '{}-{}.{}'.format(curation.id,
                                      str(time.time())+str(uuid.uuid4().hex), 'jpeg')
        map_image = ImageFile(io.BytesIO(
            get_static_naver_image(markers)), name=file_path)

        curation_map = CurationMap(
            curation=curation,
            map=map_image
        )

        curation_map.save()

    @staticmethod
    def delete(curation: Curation):
        map = CurationMap.objects.get(curation=curation)
        map.delete()
