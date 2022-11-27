import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
import haversine as hs
from places.models import Place, PlacePhoto, SNSUrl, VisitorReview, ReviewPhoto, VisitorReviewCategory
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
            #'name',
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
    
    class Meta:
        model = Place
        fields = [
            'id',
            'place_name',
            'category',
            #'vegan_category',
            #'tumblur_category',
            #'reusable_con_category',
            #'pet_category',
            'open_hours',
            #'etc_hours',
            'place_review',
            'address',
            'rep_pic',
            #'short_cur',
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
            
    def get_open_hours(self,obj):
        '''
        오늘 요일만 보내주기 위한 함수
        '''
        days = ['mon_hours','tues_hours','wed_hours','thurs_hours','fri_hours','sat_hours','sun_hours']
        a = datetime.datetime.today().weekday()
        place = Place.objects.filter(id = obj.id).values(days[a])[0]
        return place[days[a]]

    def get_place_like(self,obj):
        '''
        장소의 좋아요 여부를 알려주기 위한 함수
        '''
        re_user =  self.context['request'].user.id
        if obj.place_likeuser_set.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none'

class PlaceDetailSerializer(serializers.ModelSerializer):
    open_hours = serializers.SerializerMethodField()
    #nested serialzier -> related_names 설정 확인
    photos = PlacePhotoSerializer(many=True,read_only=True)
    sns = SNSUrlSerializer(many=True,read_only=True)
    story_id = serializers.SerializerMethodField()
    place_like = serializers.SerializerMethodField()
    class Meta:
        model = Place
        fields = [
            'id',
            'place_name',
            'category',
            #'vegan_category',
            #'tumblur_category',
            #'reusable_con_category',
            #'pet_category',
            'open_hours',
            #'etc_hours',
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
            ]
            
    def get_open_hours(self,obj):
        '''
        오늘 요일만 보내주기 위한 함수
        '''
        days = ['mon_hours','tues_hours','wed_hours','thurs_hours','fri_hours','sat_hours','sun_hours']
        a = datetime.datetime.today().weekday()
        place = Place.objects.filter(id = obj.id).values(days[a])[0]
        return place[days[a]]
        
    def get_story_id(self, obj):
        '''
            스토리 id를 보내 주기 위한 함수
        '''
        try:
            return obj.story.id
        except ObjectDoesNotExist:
            pass

    def get_place_like(self,obj):
        '''
        장소의 좋아요 여부를 알려주기 위한 함수
        '''
        re_user =  self.context['request'].user.id
        if obj.place_likeuser_set.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none' 

class VisitorReviewCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorReviewCategory
        fields = [
            'category',
            'category_choice',
        ]

class ReviewPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewPhoto
        fields = [
            'imgfile',
        ]


class VisitorReviewSerializer(serializers.ModelSerializer):
    photos = ReviewPhotoSerializer(many=True,read_only=True)
    category = VisitorReviewCategorySerializer(many=True,read_only=True)

    class Meta:
        model = VisitorReview
        fields = [
            'place',
            'visitor_name',
            'contents',
            'photos',
            'category',
            # 'created',
            # 'updated',
        ]

    # context={
    #     "request":request
    # }

    def create(self, validated_data):
        print(validated_data)
        photos_data = self.context['request'].FILES
        print(photos_data)
        review = VisitorReview.objects.create(**validated_data)
        for photo_data in photos_data.getlist('photos'):
            print(photo_data)   
            ReviewPhoto.objects.create(review=review, imgfile=photo_data)
        return review

    # def get_visitor_id(self, obj):
    #     '''
    #     작성자 id를 가지고 오기 위한 함수
    #     '''
    #     visitor = User.objects.get(id=obj.id)
    #     try:
    #         visitor.
    #         return visitor.name.id
    #     except ObjectDoesNotExist:
    #         pass

    
    # def get_visit_date(self, obj):
    #     '''
    #     작성한 날짜를 가지고 오기 위한 함수
    #     '''
    #     date = datetime.today()
    #     return date



    # def get_category(self, obj):
    #     '''
    #     장소별 카테고리를 알려주기 위한 함수
    #     '''
    #     place = Place.objects.get(id=obj.id)
    #     return place.category

