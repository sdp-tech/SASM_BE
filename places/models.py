from django.db import models
from core import models as core_models

# Create your models here.
class AbstractItem(core_models.TimeStampedModel):
    """Abstract Item"""

    name = models.CharField(max_length=80)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class Photo(core_models.TimeStampedModel):
    """Photo Model Definition"""

    image = models.URLField(max_length=3000)
    file = models.ImageField(upload_to='place/%Y%m%d/')
    place = models.ForeignKey("Place", related_name='photos',on_delete=models.CASCADE)

class SNSType(AbstractItem):
    
    pass

    class Meta:
        verbose_name = "SNS Type"

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
    tumblur_category = models.BooleanField(default=False, blank=True, null=True)
    reusable_con_category = models.BooleanField(default=False, blank=True, null=True)
    pet_category = models.BooleanField(default=False, blank=True, null=True)
    mon_hours = models.CharField(max_length=50)
    tues_hours = models.CharField(max_length=50)
    wed_hours = models.CharField(max_length=50)
    thurs_hours = models.CharField(max_length=50)
    fri_hours = models.CharField(max_length=50)
    sat_hours = models.CharField(max_length=50)
    sun_hours = models.CharField(max_length=50)
    etc_hours = models.TextField(max_length=500)
    place_review = models.CharField(max_length=200)
    sns_type = models.ManyToManyField("SNSType", related_name = 'sns')
    address = models.CharField(max_length=200)
    place_like_cnt = models.PositiveIntegerField(default=0)
    place_likeuser_set = models.ManyToManyField('users.User',related_name = 'PlaceLikeUser',blank=True)
    rep_pic = models.URLField(max_length=3000, default='')
    short_cur = models.TextField(max_length=500, default='')
    left_coordinate = models.FloatField(blank=True, null=True)
    right_coordinate = models.FloatField(blank=True, null=True)
    def __str__(self):
        return self.place_name

class SNSUrl(models.Model):
    sns_type_url = models.ForeignKey('places.SNSType', related_name ='sns_type_forurl',on_delete=models.CASCADE,null=True)
    sns_place = models.ForeignKey('places.Place', related_name ='sns', on_delete=models.CASCADE,null=True)
    sns_url = models.URLField(max_length=200,null=True)
