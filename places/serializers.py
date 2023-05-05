import io
import time
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.images import ImageFile
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

from rest_framework import serializers
import haversine as hs
from places.models import Place, PlacePhoto, SNSUrl, PlaceVisitorReview, PlaceVisitorReviewPhoto, PlaceVisitorReviewCategory, CategoryContent
from users.models import User


class PlacePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacePhoto
        fields = [
            'image',
        ]


class SNSUrlSerializer(serializers.ModelSerializer):
    # sns_name = serializers.SerializerMethodField()
    class Meta:
        model = SNSUrl
        fields = [
            # 'name',
            'url',
        ]


class MapMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = [
            'id',
            'place_name',
            'latitude',
            'longitude',
        ]


class PlaceSerializer(serializers.ModelSerializer):
    open_hours = serializers.SerializerMethodField()
    place_like = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    extra_pic = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = [
            'id',
            'place_name',
            'category',
            # 'vegan_category',
            # 'tumblur_category',
            # 'reusable_con_category',
            # 'pet_category',
            'open_hours',
            # 'etc_hours',
            'place_review',
            'address',
            'rep_pic',
            'extra_pic',
            # 'short_cur',
            'latitude',
            'longitude',
            'place_like',
            'distance',
        ]

    # #클래스 변수에 접근해야해서 classmethod 사용
    # @classmethod
    # def only_queryset(cls, queryset):
    #     queryset = queryset.values(*cls.Meta.fields)
    #     return queryset

    def get_distance(self, obj):
        '''
            거리순 정렬을 위해 거리를 계산하는 함수
        '''
        left = self.context.get('left')
        right = self.context.get('right')
        my_location = (float(left), float(right))
        place_location = (obj.latitude, obj.longitude)
        distance = hs.haversine(my_location, place_location)
        return float(distance)

    def get_open_hours(self, obj):
        '''
        오늘 요일만 보내주기 위한 함수
        '''
        days = ['mon_hours', 'tues_hours', 'wed_hours',
                'thurs_hours', 'fri_hours', 'sat_hours', 'sun_hours']
        a = datetime.datetime.today().weekday()
        place = Place.objects.filter(id=obj.id).values(days[a])[0]
        return place[days[a]]

    def get_place_like(self, obj):
        '''
        장소의 좋아요 여부를 알려주기 위한 함수
        '''
        re_user = self.context['request'].user.id
        if obj.place_likeuser_set.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none'

    def get_extra_pic(self, obj):
        photos = PlacePhoto.objects.filter(
            place=obj).annotate(
            imageUrls=Concat(Value(settings.MEDIA_URL),
                             F('image'),
                             output_field=CharField())
        ).values_list('imageUrls', flat=True)
        return photos


class PlaceDetailSerializer(serializers.ModelSerializer):
    open_hours = serializers.SerializerMethodField()
    # nested serialzier -> related_names 설정 확인
    photos = PlacePhotoSerializer(many=True, read_only=True)
    sns = SNSUrlSerializer(many=True, read_only=True)
    story_id = serializers.SerializerMethodField()
    place_like = serializers.SerializerMethodField()
    category_statistics = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = [
            'id',
            'place_name',
            'category',
            'vegan_category',
            'tumblur_category',
            'reusable_con_category',
            'pet_category',
            'open_hours',
            # 'etc_hours',
            'mon_hours',
            'tues_hours',
            'wed_hours',
            'thurs_hours',
            'fri_hours',
            'sat_hours',
            'sun_hours',
            'place_review',
            'address',
            'rep_pic',
            'short_cur',
            'latitude',
            'longitude',
            'photos',
            'sns',
            'story_id',
            'place_like',
            'category_statistics',
            'phone_num',
        ]

    def get_open_hours(self, obj):
        '''
        오늘 요일만 보내주기 위한 함수
        '''
        days = ['mon_hours', 'tues_hours', 'wed_hours',
                'thurs_hours', 'fri_hours', 'sat_hours', 'sun_hours']
        a = datetime.datetime.today().weekday()
        place = Place.objects.filter(id=obj.id).values(days[a])[0]
        return place[days[a]]

    def get_story_id(self, obj):
        '''
            스토리 id를 보내 주기 위한 함수
        '''
        try:
            return obj.story.id
        except ObjectDoesNotExist:
            pass

    def get_place_like(self, obj):
        '''
        장소의 좋아요 여부를 알려주기 위한 함수
        '''
        re_user = self.context['request'].user.id
        if obj.place_likeuser_set.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none'

    def get_category_statistics(self, obj):
        TOP_COUNTS = 3
        statistic = []
        place_review_category_total, category_count = self.count_place_review_category(
            obj)
        category_count = sorted(category_count.items(),
                                key=lambda x: x[1], reverse=True)[:TOP_COUNTS]
        for i in category_count:
            l = [i[0], round(i[1]/place_review_category_total*100)]
            statistic.append(l)
        return statistic

    def count_place_review_category(self, place):
        count = 0
        category_count = {}
        l = PlaceVisitorReview.objects.filter(
            place=place).prefetch_related('category')
        for visitor_review_obj in l:
            # 역참조
            p = visitor_review_obj.category.all()
            for visitor_review_category_obj in p:
                count += 1
                category_content = visitor_review_category_obj.category.category_content
                category_count = self.is_in_category_count(
                    category_content, category_count)
        return count, category_count

    def is_in_category_count(self, category_content, category_count):
        if category_content in category_count.keys():
            category_count[category_content] += 1
            return category_count
        category_count[category_content] = 1
        return category_count


class VisitorReviewCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceVisitorReviewCategory
        fields = [
            'category',
            # 'category_choice',
        ]


class ReviewPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceVisitorReviewPhoto
        fields = [
            'imgfile',
        ]


class VisitorReviewSerializer(serializers.ModelSerializer):
    photos = ReviewPhotoSerializer(many=True, read_only=True)
    category = VisitorReviewCategorySerializer(many=True, read_only=True)
    nickname = serializers.SerializerMethodField()
    # category_statistics = serializers.SerializerMethodField()
    writer = serializers.SerializerMethodField()

    class Meta:
        model = PlaceVisitorReview
        fields = [
            'id',
            'nickname',
            'place',
            'contents',
            'photos',
            'category',
            'created',
            'updated',
            # 'category_statistics',
            'writer',
        ]

    def get_nickname(self, obj):
        return obj.visitor_name.nickname

    def get_writer(self, obj):
        return obj.visitor_name.email

    def create(self, validated_data):
        photos_data = self.context['request'].FILES
        user = self.context['request'].user
        review = PlaceVisitorReview.objects.create(
            **validated_data, visitor_name=user)
        photos = photos_data.getlist('photos')
        count = len(photos)
        if (count > 3):
            raise serializers.ValidationError()
        for photo_data in photos:
            # 파일 경로 설정
            ext = photo_data.name.split(".")[-1]
            file_path = '{}/{}/{}.{}'.format(
                validated_data['place'], review.id, str(datetime.datetime.now()), ext)
            image = ImageFile(io.BytesIO(photo_data.read()), name=file_path)
            PlaceVisitorReviewPhoto.objects.create(
                review=review, imgfile=image)
        for category_data in self.context['request'].POST.getlist('category')[0].split(','):
            try:
                instance = PlaceVisitorReviewCategory.objects.create(
                    category_id=category_data)
                instance.category_choice.add(review)
            except Exception as e:
                print(e)
        return review

    def update(self, instance, validated_data):
        category = self.context['request'].data['category'].split(',')
        p = instance.category.all()
        count = 0
        for visitor_review_category_obj in p:
            if visitor_review_category_obj.category.id != category[count]:
                visitor_review = PlaceVisitorReviewCategory.objects.create(
                    category_id=category[count])
                visitor_review.category_choice.add(instance)
                visitor_review_category_obj.delete()
            count += 1
        if (self.context['request'].FILES):
            print('dd')
        instance.contents = validated_data.get('contents', instance.contents)
        instance.save()
        return instance

    def validate(self, data):
        if self.context['request'].POST.getlist('category') != ['']:
            for category_data in self.context['request'].POST.getlist('category')[0].split(','):
                instance = CategoryContent.objects.get(id=category_data)
                if (instance.category_group == '공통'):
                    continue
                if (data['place'].category != instance.category_group):
                    raise serializers.ValidationError(
                        "장소 리뷰와 장소의 category가 일치하지 않습니다.")
        return data
