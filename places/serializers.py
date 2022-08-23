from django.contrib.auth import get_user_model
from rest_framework import serializers
from places.models import Place, Photo, SNSUrl

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = [
            'image',
        ]

class SNSUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = SNSUrl
        fields = [
            'sns_type_url',
            'sns_url',
        ]

class PlaceSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True,read_only=True)
    sns = SNSUrlSerializer(many=True,read_only=True)
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
            'mon_hours',
            'tues_hours',
            'wed_hours',
            'thurs_hours',
            'fri_hours',
            'sat_hours',
            'sun_hours',
            'etc_hours',
            'place_review',
            'address',
            'rep_pic',
            'short_cur',
            'left_coordinate',
            'right_coordinate',
            'photos',
            'sns',
            ]
