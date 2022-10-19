import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
import haversine as hs
from places.models import Place, PlacePhoto, SNSUrl
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
            'vegan_category',
            'tumblur_category',
            'reusable_con_category',
            'pet_category',
            'open_hours',
            'etc_hours',
            'place_review',
            'address',
            'rep_pic',
            'short_cur',
            'latitude',
            'longitude',
            'place_like',
            'distance',
        ]
        
    def get_distance(self, obj):
        '''
            거리순 정렬을 위해 거리를 계산하는 함수
        '''
        left = self.context.get('left')
        right = self.context.get('right')
        
        my_location = (float(left), float(right))
        
        place = Place.objects.get(id=obj.id)
        place_location = (place.latitude, place.longitude)
        distance = hs.haversine(my_location, place_location)
        return float(distance)
            
    def get_open_hours(self,obj):
        '''
        오늘 요일만 보내주기 위한 함수
        '''
        days = ['mon_hours','tues_hours','wed_hours','thurs_hours','fri_hours','sat_hours','sun_hours']
        a = datetime.datetime.today().weekday()
        place = Place.objects.filter(id=obj.id).values(days[a])[0]
        return place[days[a]]

    def get_place_like(self,obj):
        '''
        장소의 좋아요 여부를 알려주기 위한 함수
        '''
        place = Place.objects.get(id=obj.id)
        re_user =  self.context['request'].user.id
        like_id = place.place_likeuser_set.all()
        users = User.objects.filter(id__in=like_id)
        if users.filter(id=re_user).exists():
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
            'vegan_category',
            'tumblur_category',
            'reusable_con_category',
            'pet_category',
            'open_hours',
            'etc_hours',
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
        place = Place.objects.filter(id=obj.id).values(days[a])[0]
        return place[days[a]]
    
    def get_story_id(self, obj):
        '''
            스토리 id를 보내 주기 위한 함수
        '''
        place = Place.objects.get(id=obj.id)
        try:
            place.story
            return place.story.id
        except ObjectDoesNotExist:
            pass

    def get_place_like(self,obj):
        '''
        장소의 좋아요 여부를 알려주기 위한 함수
        '''
        place = Place.objects.get(id=obj.id)
        re_user =  self.context['request'].user.id
        like_id = place.place_likeuser_set.all()
        users = User.objects.filter(id__in=like_id)
        if users.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none' 
