from django.db import models
from django.core.exceptions import ValidationError
from django.dispatch import receiver

from core.models import TimeStampedModel


class Category(models.Model):
    name = models.CharField(max_length=200)


class SemiCategory(TimeStampedModel):
    name = models.CharField(max_length=10)
    category = models.ForeignKey(
        'Category', related_name='semicategories', on_delete=models.CASCADE, null=False, blank=False)
    forest = models.ManyToManyField(
        "Forest", related_name='semicategories', blank=True)


def validate_str_field_length(target: str):
    # string 필드가 공백을 제외한 길이가 1 이상인지 확인
    # 1. 길이가 0인 내용이 저장되는 것을 방지
    # 2. 길이가 1 이상이나 공백으로만 이루어진 것을 저장하는 것을 방지

    without_white_spaces = target.replace(' ', '')
    return not without_white_spaces


class ForestHashtag(TimeStampedModel):
    name = models.CharField(max_length=10)
    forest = models.ForeignKey(
        'Forest', related_name='hashtags', on_delete=models.CASCADE, null=False, blank=False)

    def clean(self):
        if validate_str_field_length(self.name):
            raise ValidationError('해시태그의 이름은 공백 제외 최소 1글자 이상이어야 합니다.')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'forest'], name='forest_can_have_hashtag_with_unique_name_constraint'),
        ]


def get_forest_rep_pic_upload_path(instance, filename):
    return 'forest/rep_pic/{}'.format(filename)


class Forest(TimeStampedModel):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(
        max_length=200, blank=True)
    content = models.TextField(max_length=50000)
    category = models.ForeignKey(
        'Category', related_name='forests', on_delete=models.CASCADE, null=False, blank=False)
    writer = models.ForeignKey(
        'users.User', related_name='forests', on_delete=models.SET_NULL, null=True, blank=False)
    likeuser_set = models.ManyToManyField(
        "users.User", related_name='liked_forests', blank=True)
    like_cnt = models.PositiveIntegerField(default=0)
    view_cnt = models.PositiveIntegerField(default=0)

    rep_pic = models.ImageField(
        upload_to=get_forest_rep_pic_upload_path, default='forest_rep_pic.png')

    def clean(self):
        if validate_str_field_length(self.title):
            raise ValidationError('포레스트의 제목은 공백 제외 최소 1글자 이상이어야 합니다.')

        if validate_str_field_length(self.content):
            raise ValidationError('포레스트의 내용은 공백 제외 최소 1글자 이상이어야 합니다.')

    def like(self):
        self.like_cnt += 1

    def dislike(self):
        self.like_cnt -= 1


@receiver(models.signals.pre_delete, sender=Forest)
# Forest가 삭제되기 전(pre_delete), S3 media에서 rep_pic 이미지 파일을 삭제하여 orphan 이미지 파일이 남지 않도록 처리
def remove_forest_rep_pic_from_s3(sender, instance, using, **kwargs):
    instance.rep_pic.delete(save=False)


def get_forest_photo_upload_path(instance, filename):
    return 'forest/post/{}'.format(filename)


class ForestPhoto(TimeStampedModel):
    image = models.ImageField(
        upload_to=get_forest_photo_upload_path, default='forest_image.png')
    forest = models.ForeignKey(
        'Forest', related_name='photos', on_delete=models.CASCADE, null=True, blank=True)


@receiver(models.signals.post_delete, sender=ForestPhoto)
# ForestPhoto가 삭제된 후(post_delete), S3 media에서 이미지 파일을 삭제하여 orphan 이미지 파일이 남지 않도록 처리
# ref. https://stackoverflow.com/questions/47377172/django-storages-aws-s3-delete-file-from-model-record
def remove_forest_photo_from_s3(sender, instance, using, **kwargs):
    instance.image.delete(save=False)


class ForestReport(TimeStampedModel):
    """Forest Report Category Definition"""
    FOREST_REPORT1 = "지나친 광고성 컨텐츠입니다.(상업적 홍보)"
    FOREST_REPORT2 = "욕설이 포함된 컨텐츠입니다."
    FOREST_REPORT3 = "성희롱이 포함된 컨텐츠입니다."
    FOREST_REPORT_CATEGORY_CHOICES = (
        (FOREST_REPORT1, "지나친 광고성 컨텐츠입니다.(상업적 홍보)"),
        (FOREST_REPORT2, "욕설이 포함된 컨텐츠입니다."),
        (FOREST_REPORT3, "성희롱이 포함된 컨텐츠입니다.")
    )
    category = models.CharField(
        choices=FOREST_REPORT_CATEGORY_CHOICES, max_length=30, blank=False)
    forest = models.ForeignKey(
        'Forest', related_name='reports', on_delete=models.CASCADE, null=True, blank=False)
    reporter = models.ForeignKey(
        'users.User', related_name='forest_reports', on_delete=models.SET_NULL, null=True, blank=False)


class ForestComment(TimeStampedModel):
    forest = models.ForeignKey(
        "Forest", related_name='comments', on_delete=models.CASCADE, null=False, blank=False)
    content = models.TextField(max_length=1000)
    # 댓글 writer가 회원 탈퇴해도, 댓글은 유지, writer를 null 설정
    writer = models.ForeignKey(
        'users.User', related_name='forest_comments', on_delete=models.SET_NULL, null=True, blank=False)
    likeuser_set = models.ManyToManyField(
        "users.User", related_name='liked_forest_comments', blank=True)
    like_cnt = models.PositiveIntegerField(default=0)
