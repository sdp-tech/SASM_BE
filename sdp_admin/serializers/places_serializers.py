import time
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth import get_user_model
from places.models import Place, PlacePhoto,SNSType,SNSUrl
from users.models import User
# from places.models import Place
class SNSUrlAdminSerializer(serializers.ModelSerializer):
    snstype_name = serializers.SerializerMethodField()
    class Meta:
        model = SNSUrl
        fields = [
            'url',
            'place',
            'snstype',
            'snstype_name',
        ]
    def get_snstype_name(self,obj):
        snstype = SNSUrl.objects.get(id=obj.id).snstype
        return snstype.name


class PlacesAdminSerializer(serializers.ModelSerializer):

    class Meta:
        model = Place
        ordering = ['-id']
        fields = [
            'id',
            'place_name',
            'category',
            'vegan_category',
            'tumblur_category',
            'reusable_con_category',
            'pet_category',
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
            'phone_num',
        ]

    def change_rep_pic_name(self, place, validated_data):
        place_name = validated_data['place_name']
        ext = place.rep_pic.name.split(".")[-1]
        place.rep_pic.name = 'places/{}/{}.{}'.format(place_name, 'rep', ext)

    def create(self, validated_data):
        # validated_data 내 rep_pic의 이름 변경이 원활하게 되지 않아 DRY한 방법으로 구현
        place = Place(**validated_data)

        self.change_rep_pic_name(place, validated_data)
        place.save()

        return place

    def update(self, instance, validated_data):
        # validated_data 내 rep_pic의 이름 변경이 원활하게 되지 않아 DRY한 방법으로 구현
        print(validated_data)
        fields = instance._meta.fields
        for field in fields:
            field = field.name.split('.')[-1]  # to get coulmn name
            # rep_pic이 업데이트되지 않았을 경우 skip
            if field == 'rep_pic' and 'rep_pic' not in validated_data:
                continue
            exec("instance.%s = validated_data.get(field, instance.%s)" %
                (field, field))

        # rep_pic이 업데이트되었을 때 실행
        if 'rep_pic' in validated_data:
            self.change_rep_pic_name(instance, validated_data)
        instance.save()
        return instance


class PlacePhotoAdminSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = PlacePhoto
        fields = [
            'image',
            'place',
        ]


class SNSTypeAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = SNSType
        fields = [
            'id',
            'name',
        ]
