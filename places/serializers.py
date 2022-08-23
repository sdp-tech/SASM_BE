from django.contrib.auth import get_user_model
from rest_framework import serializers
from places import models as place_models

class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = place_models.Place
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
            ]