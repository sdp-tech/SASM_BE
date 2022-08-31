from django.db import models
from core import models as core_models

# Create your models here.
class SNSUrl(models.Model):
    url = models.URLField(max_length=200)
    place = models.ManyToManyField("Place",related_name='place_sns_url')
    snstype = models.ForeignKey("SNSType",on_delete=models.CASCADE)

class SNSType(core_models.TimeStampedModel):
    
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name

class PlacePhoto(core_models.TimeStampedModel):
    """PlacePhoto Model Definition"""
    image = models.URLField(max_length=200)
    place = models.ForeignKey("Place",on_delete=models.CASCADE)

class Place(core_models.TimeStampedModel):
    """Place Model Definition"""
    PLACE1 = "식당 및 카페"
    PLACE2 = "전시 및 체험공간"
    PLACE3 = "제로웨이스트 샵"
    PLACE4 = "도시 재생 및 친환경 건출물"
    PLACE5 = "복합 문화 공간"
    PLACE6 = "녹색 공간"
    PLACE7 = "그 외"
    PLACE_CHOICES = (
        (PLACE1, "식당 및 카페"),
        (PLACE2, "전시 및 체험공간"),
        (PLACE3, "제로웨이스트 샵"),
        (PLACE4, "도시 재생 및 친환경 건출물"),
        (PLACE5, "복합 문화 공간"),
        (PLACE6, "녹색 공간"),
        (PLACE7, "그 외"),
    )
    VEGAN1 = "비건"
    VEGAN2 = "락토"
    VEGAN3 = "오보"
    VEGAN4 = "페스코"
    VEGAN5 = "폴로"
    VEGAN6 = "그 외"
    VEGAN_CHOICES = (
        (VEGAN1, "비건"),
        (VEGAN2, "락토"),
        (VEGAN3, "오보"),
        (VEGAN4, "페스코"),
        (VEGAN5, "폴로"),
        (VEGAN6, "그 외"),
    )
    
    place_name = models.CharField(max_length=100)
    category = models.CharField(choices=PLACE_CHOICES, max_length=30, blank=True)
    vegan_category = models.CharField(choices=VEGAN_CHOICES, max_length=10, blank=True)
    tumblur_category = models.BooleanField(null=True, blank=True)
    reusable_con_category = models.BooleanField(null=True, blank=True)
    pet_category = models.BooleanField(null=True, blank=True)
    mon_hours = models.CharField(max_length=100)
    tues_hours = models.CharField(max_length=100)
    wed_hours = models.CharField(max_length=100)
    thurs_hours = models.CharField(max_length=100)
    fri_hours = models.CharField(max_length=100)
    sat_hours = models.CharField(max_length=100)
    sun_hours = models.CharField(max_length=100)
    etc_hours = models.TextField(max_length=500)
    place_review = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    place_like_cnt = models.PositiveIntegerField(default=0)
    place_likeuser_set = models.ManyToManyField('users.User', related_name='PlaceLikeUser', blank=True)
    rep_pic = models.URLField(max_length=300, blank=True)
    short_cur = models.TextField(max_length=500, blank=True)
    left_coordinate = models.FloatField(blank=True)
    right_coordinate = models.FloatField(blank=True)
    phone_num = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.place_name