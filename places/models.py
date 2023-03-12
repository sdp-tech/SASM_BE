from django.db import models
from core import models as core_models
from django.dispatch import receiver

# Create your models here.
class SNSUrl(models.Model):
    url = models.URLField(max_length=200)
    place = models.ForeignKey("Place",related_name='place_sns_url',on_delete=models.CASCADE)
    snstype = models.ForeignKey("SNSType",on_delete=models.CASCADE)

    def __str__(self):
        return self.place.place_name

class SNSType(core_models.TimeStampedModel):
    
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name


def get_upload_path(instance, filename):
    return 'places/{}'.format(filename)
class PlacePhoto(core_models.TimeStampedModel):
    """PlacePhoto Model Definition"""
    image = models.ImageField(
        upload_to=get_upload_path, default='place_image.png')
    place = models.ForeignKey("Place", related_name='photos', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.place.place_name
    

class Place(core_models.TimeStampedModel):
    """Place Model Definition"""
    PLACE1 = "식당 및 카페"
    PLACE2 = "전시 및 체험공간"
    PLACE3 = "제로웨이스트 샵"
    PLACE4 = "도시 재생 및 친환경 건축물"
    PLACE5 = "복합 문화 공간"
    PLACE6 = "녹색 공간"
    PLACE7 = "그 외"
    PLACE_CHOICES = (
        (PLACE1, "식당 및 카페"),
        (PLACE2, "전시 및 체험공간"),
        (PLACE3, "제로웨이스트 샵"),
        (PLACE4, "도시 재생 및 친환경 건축물"),
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
    etc_hours = models.TextField(max_length=500, blank=True)
    place_review = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    place_like_cnt = models.PositiveIntegerField(default=0)
    place_likeuser_set = models.ManyToManyField('users.User', related_name='PlaceLikeUser', blank=True)
    rep_pic = models.ImageField()
    short_cur = models.TextField(max_length=500, blank=True)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    phone_num = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.place_name


class CategoryContent(models.Model):
    COMMON = "공통"
    PLACE1 = "식당 및 카페"
    PLACE2 = "전시 및 체험공간"
    PLACE3 = "제로웨이스트 샵"
    PLACE4 = "도시 재생 및 친환경 건축물"
    PLACE5 = "복합 문화 공간"
    PLACE6 = "녹색 공간"
    PLACE7 = "그 외"
    PLACE_CHOICES = (
        (COMMON, "공통"),
        (PLACE1, "식당 및 카페"),
        (PLACE2, "전시 및 체험공간"),
        (PLACE3, "제로웨이스트 샵"),
        (PLACE4, "도시 재생 및 친환경 건축물"),
        (PLACE5, "복합 문화 공간"),
        (PLACE6, "녹색 공간"),
        (PLACE7, "그 외"),
    )

    category_content = models.CharField(max_length=100)
    category_group = models.CharField(choices=PLACE_CHOICES, max_length=30, blank=True)

    def __str__(self):
        return self.category_content

class PlaceVisitorReviewCategory(core_models.TimeStampedModel):
    # place_category = models.CharField(max_length=80)
    category = models.ForeignKey("CategoryContent", on_delete=models.CASCADE)
    category_choice = models.ManyToManyField("PlaceVisitorReview", related_name='category')

    # def __str__(self):
    #     return self.category

class PlaceVisitorReview(core_models.TimeStampedModel):
    place = models.ForeignKey("Place", on_delete=models.CASCADE) #방문자리뷰 모델은 Place 모델을 속성으로 가져야 함
    visitor_name = models.ForeignKey("users.User", on_delete=models.CASCADE)  #리뷰다는 사람 이름
    contents = models.TextField(help_text="리뷰를 작성해주세요.", blank=False, null=False) #내용 작성

    def __str__(self):
        return self.contents

    def update_contents(self, contents):
        self.contents = contents

def image_upload_path(instance, filename):
    return 'reviewphoto/{}'.format(filename)

class PlaceVisitorReviewPhoto(core_models.TimeStampedModel):
    imgfile = models.ImageField(null=True, upload_to=image_upload_path, blank=True)
    review = models.ForeignKey("PlaceVisitorReview", related_name='photos', on_delete=models.CASCADE)

@receiver(models.signals.post_delete, sender=PlaceVisitorReviewPhoto)
# PlaceReviewPhoto가 삭제된 후(place_review_delete), S3 media에서 이미지 파일을 삭제하여 orphan 이미지 파일이 남지 않도록 처리
# ref. https://stackoverflow.com/questions/47377172/django-storages-aws-s3-delete-file-from-model-record
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.imgfile.delete(save=False)