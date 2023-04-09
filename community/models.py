from django.db import models
from django.core.exceptions import ValidationError
from django.dispatch import receiver

from core.models import TimeStampedModel


class Board(models.Model):
    name = models.CharField(max_length=200)
    supports_hashtags = models.BooleanField(
        null=False, blank=False, default=False)
    supports_post_photos = models.BooleanField(
        null=False, blank=False, default=False)
    supports_post_comment_photos = models.BooleanField(
        null=False, blank=False, default=False)
    supports_post_comments = models.BooleanField(
        null=False, blank=False, default=False)

    # 게시판이 사용하는 글 양식 지정
    post_content_style = models.ForeignKey(
        'PostContentStyle', related_name='applied_boards', on_delete=models.SET_NULL, null=True, blank=True)


def validate_str_field_length(target: str):
    # string 필드가 공백을 제외한 길이가 1 이상인지 확인
    # 1. 길이가 0인 내용이 저장되는 것을 방지
    # 2. 길이가 1 이상이나 공백으로만 이루어진 것을 저장하는 것을 방지

    without_white_spaces = target.replace(' ', '')
    return not without_white_spaces


class Post(TimeStampedModel):
    title = models.CharField(max_length=200)
    content = models.TextField(max_length=50000)
    board = models.ForeignKey(  # 정보글에선 카테고리에 해당
        'Board', related_name='posts', on_delete=models.CASCADE, null=False, blank=False)
    writer = models.ForeignKey(
        'users.User', related_name='posts', on_delete=models.SET_NULL, null=True, blank=False)
    like_cnt = models.PositiveIntegerField(default=0)
    view_cnt = models.PositiveIntegerField(default=0)

    # 정보글 관련 필드
    subtitle = models.CharField(max_length=200, default="없음")  # 소제목
    keyword = models.CharField(max_length=100, default="없음")  # 키워드

    # ForeignKey와 같은 relational 필드를 제외한 non-relational 필드에 대한 기본적이고 간단한 검증 로직 포함
    # 복잡한 필드 검증이나 모델 필드 외 데이터에 대한 검증, 필드 관계 검증은 Serivce/Serializer에서 수행
    def clean(self):
        if validate_str_field_length(self.title):
            raise ValidationError('게시글의 제목은 공백 제외 최소 1글자 이상이어야 합니다.')

        if validate_str_field_length(self.content):
            raise ValidationError('게시글의 내용은 공백 제외 최소 1글자 이상이어야 합니다.')

        # self.content = self.content.replace("\r\n", "")

    def entire_update(self, title, content, subtitle, keyword):
        self.title = title
        self.content = content
        self.subtitle = subtitle
        self.keyword = keyword

    def like(self):
        self.like_cnt += 1

    def dislike(self):
        self.like_cnt -= 1


class PostPlace(TimeStampedModel):
    post = models.ForeignKey('Post', related_name='places',
                             on_delete=models.CASCADE, null=False, blank=False)
    name = models.CharField(max_length=200)  # 장소명
    address = models.CharField(max_length=200)  # 장소 주소(지번, 도로명)
    contact = models.CharField(max_length=200)  # 장소 연락처
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)


class PostContentStyle(TimeStampedModel):
    name = models.CharField(max_length=50)
    styled_content = models.TextField(max_length=50000)


class PostHashtag(TimeStampedModel):
    name = models.CharField(max_length=10)
    post = models.ForeignKey(
        'Post', related_name='hashtags', on_delete=models.CASCADE, null=False, blank=False)

    def clean(self):
        if validate_str_field_length(self.name):
            raise ValidationError('해시태그의 이름은 공백 제외 최소 1글자 이상이어야 합니다.')

    # 필드 name, post 조합을 unique key로 설정하여, 한 게시글이 중복된 이름을 가지는 해시태그를 가질 수 없도록 제한
    # service 레이어에서 1차적으로 검증하나, 일관성을 좀 더 강력히 보장하고, 도메인 지식을 model 레이어에 담기 위해 추가
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'post'], name='post_can_have_hashtag_with_unique_name_constraint'),
        ]


def get_post_photo_upload_path(instance, filename):
    return 'community/post/{}'.format(filename)


class PostPhoto(TimeStampedModel):
    image = models.ImageField(
        upload_to=get_post_photo_upload_path, default='post_image.png')
    post = models.ForeignKey(
        'Post', related_name='photos', on_delete=models.CASCADE, null=False, blank=False)


@receiver(models.signals.post_delete, sender=PostPhoto)
# PostPhoto가 삭제된 후(post_delete), S3 media에서 이미지 파일을 삭제하여 orphan 이미지 파일이 남지 않도록 처리
# ref. https://stackoverflow.com/questions/47377172/django-storages-aws-s3-delete-file-from-model-record
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.image.delete(save=False)


class PostLike(TimeStampedModel):
    post = models.ForeignKey(
        'Post', related_name='likes', on_delete=models.CASCADE, null=False, blank=False)
    user = models.ForeignKey(
        'users.User', related_name='post_likes', on_delete=models.SET_NULL, null=True, blank=False)  # 좋아요를 누른 사용자가 삭제되어도 좋아요는 유지

    # 필드 post, user 조합을 unique key로 설정하여, 한 유저가 한 게시글에 대해 단 한번만 좋아요를 할 수 있도록 제한
    # service 레이어에서 1차 검증을 하나, 일관성을 좀 더 강력히 보장하고, 도메인 지식을 model 레이어에 담기 위해 추가
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'], name='user_can_like_post_only_once_constraint'),
        ]


class PostComment(TimeStampedModel):
    post = models.ForeignKey(
        'Post', related_name='comments', on_delete=models.CASCADE, null=False, blank=False)
    content = models.TextField(max_length=1000)
    # isParent: true일 경우 parent 댓글, false일 경우 child 댓글
    isParent = models.BooleanField(null=False, blank=False, default=True)
    # parent 댓글이 삭제되어도, child 댓글은 유지, parent를 null 설정
    parent = models.ForeignKey(
        'PostComment', related_name='child_comments', on_delete=models.SET_NULL, null=True, blank=True)
    # 댓글 writer가 회원 탈퇴해도, 댓글은 유지, writer를 null 설정
    writer = models.ForeignKey(
        'users.User', related_name='post_comments', on_delete=models.SET_NULL, null=True, blank=False)
    # 멘션된 사용자가 회원 탈퇴하더라도, 댓글은 유지, mention을 null 설정
    mention = models.ForeignKey(
        'users.User', related_name='mentioned_post_comments', on_delete=models.SET_NULL, null=True, blank=True)

    def update_content(self, content):
        self.content = content

    def update_mention(self, mention):
        self.mention = mention


def get_comment_photo_upload_path(instance, filename):
    return 'community/post_comment/{}'.format(filename)


class PostCommentPhoto(TimeStampedModel):
    image = models.ImageField(
        upload_to=get_comment_photo_upload_path, default='post_comment_image.png')
    post_comment = models.ForeignKey(
        'PostComment', related_name='photos', on_delete=models.CASCADE, null=False, blank=False)


@receiver(models.signals.post_delete, sender=PostCommentPhoto)
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.image.delete(save=False)


class PostReport(TimeStampedModel):
    """Post Report Category Definition"""
    POST_REPORT1 = "게시판 성격에 부적절함"
    POST_REPORT2 = "음란물/불건전한 만남 및 대화"
    POST_REPORT3 = "사칭/사기성 게시글"
    POST_REPORT4 = "욕설/비하"
    POST_REPORT5 = "낚시/도배성 게시글"
    POST_REPORT6 = "상업적 광고 및 판매"
    POST_REPORT_CATEGORY_CHOICES = (
        (POST_REPORT1, "게시판 성격에 부적절함"),
        (POST_REPORT2, "음란물/불건전한 만남 및 대화"),
        (POST_REPORT3, "사칭/사기성 게시글"),
        (POST_REPORT4, "욕설/비하"),
        (POST_REPORT5, "낚시/도배성 게시글"),
        (POST_REPORT6, "상업적 광고 및 판매"),
    )
    category = models.CharField(
        choices=POST_REPORT_CATEGORY_CHOICES, max_length=30, blank=False)
    post = models.ForeignKey(
        'Post', related_name='reports', on_delete=models.CASCADE, null=True, blank=False)
    reporter = models.ForeignKey(
        'users.User', related_name='post_reports', on_delete=models.SET_NULL, null=True, blank=False)


class PostCommentReport(TimeStampedModel):
    """Post Comment Report Category Definition"""
    POST_COMMENT_REPORT1 = "음란물/불건전한 만남 및 대화"
    POST_COMMENT_REPORT2 = "사칭/사기성 댓글"
    POST_COMMENT_REPORT3 = "욕설/비하"
    POST_COMMENT_REPORT4 = "낚시/도배성 댓글"
    POST_COMMENT_REPORT5 = "상업적 광고 및 판매"
    POST_COMMENT_REPORT_CATEGORY_CHOICES = (
        (POST_COMMENT_REPORT1, "음란물/불건전한 만남 및 대화"),
        (POST_COMMENT_REPORT2, "사칭/사기성 댓글"),
        (POST_COMMENT_REPORT3, "욕설/비하"),
        (POST_COMMENT_REPORT4, "낚시/도배성 댓글"),
        (POST_COMMENT_REPORT5, "상업적 광고 및 판매"),
    )
    category = models.CharField(
        choices=POST_COMMENT_REPORT_CATEGORY_CHOICES, max_length=30, blank=False)
    comment = models.ForeignKey(
        'PostComment', related_name='reports', on_delete=models.CASCADE, null=True, blank=False)
    reporter = models.ForeignKey(
        'users.User', related_name='post_comment_reports', on_delete=models.SET_NULL, null=True, blank=False)
