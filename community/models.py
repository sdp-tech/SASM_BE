from django.db import models
from django.core.exceptions import ValidationError
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


def validate_str_field_length(target: str):
    # string 필드가 공백을 제외한 길이가 1 이상인지 확인
    # 1. 길이가 0인 내용이 저장되는 것을 방지
    # 2. 길이가 1 이상이나 공백으로만 이루어진 것을 저장하는 것을 방지

    without_white_spaces = target.replace(' ', '')
    return not without_white_spaces


class Post(TimeStampedModel):
    title = models.CharField(max_length=200)
    content = models.TextField(max_length=50000)
    board = models.ForeignKey(
        'Board', related_name='posts', on_delete=models.CASCADE, null=False, blank=False)
    writer = models.ForeignKey(
        'users.User', related_name='posts', on_delete=models.SET_NULL, null=True, blank=False)
    like_cnt = models.PositiveIntegerField(default=0)
    view_cnt = models.PositiveIntegerField(default=0)
    comment_cnt = models.PositiveIntegerField(default=0)

    # ForeignKey와 같은 relational 필드를 제외한 non-relational 필드에 대한 기본적이고 간단한 검증 로직 포함
    # 복잡한 필드 검증이나 모델 필드 외 데이터에 대한 검증, 필드 관계 검증은 Serivce/Serializer에서 수행
    def clean(self):
        if validate_str_field_length(self.title):
            raise ValidationError('게시글의 제목은 공백 제외 최소 1글자 이상이어야 합니다.')

        if validate_str_field_length(self.content):
            raise ValidationError('게시글의 내용은 공백 제외 최소 1글자 이상이어야 합니다.')

        # self.content = self.content.replace("\r\n", "")

    @property
    def get_like_count(self):
        return self.like_cnt

    @property
    def get_view_count(self):
        return self.view_cnt

    @property
    def set_title(self, title):
        self.title = title

    @property
    def set_content(self, content):
        self.content = content


class PostHashtag(TimeStampedModel):
    name = models.CharField(max_length=10)
    post = models.ForeignKey(
        'Post', related_name='hashtags', on_delete=models.CASCADE, null=False, blank=False)

    def clean(self):
        if validate_str_field_length(self.name):
            raise ValidationError('해시태그의 이름은 공백 제외 최소 1글자 이상이어야 합니다.')


def get_post_photo_upload_path(instance, filename):
    return 'community/post/{}'.format(filename)


class PostPhoto(TimeStampedModel):
    image = models.ImageField(
        upload_to=get_post_photo_upload_path, default='post_image.png')
    post = models.ForeignKey(
        'Post', related_name='photos', on_delete=models.CASCADE, null=False, blank=False)


class PostLike(TimeStampedModel):
    post = models.ForeignKey(
        'Post', related_name='likes', on_delete=models.CASCADE, null=False, blank=False)
    user = models.ForeignKey(
        'users.User', related_name='post_likes', on_delete=models.SET_NULL, null=True, blank=False)  # 좋아요를 누른 사용자가 삭제되어도 좋아요는 유지


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


def get_comment_photo_upload_path(instance, filename):
    return 'community/post_comment/{}'.format(filename)


class PostCommentPhoto(TimeStampedModel):
    image = models.ImageField(
        upload_to=get_comment_photo_upload_path, default='post_comment_image.png')
    comment = models.ForeignKey(
        'PostComment', related_name='photos', on_delete=models.CASCADE, null=False, blank=False)


class Report(TimeStampedModel):
    """Report Category Definition"""
    REPORT1 = "게시판 성격에 부적절함"
    REPORT2 = "음란물/불건전한 만남 및 대화"
    REPORT3 = "사칭/사기성 게시글"
    REPORT4 = "욕설/비하"
    REPORT5 = "낚시/도배성 게시글"
    REPORT6 = "상업적 광고 및 판매"
    REPORT_CATEGORY_CHOICES = (
        (REPORT1, "게시판 성격에 부적절함"),
        (REPORT2, "음란물/불건전한 만남 및 대화"),
        (REPORT3, "사칭/사기성 게시글"),
        (REPORT4, "욕설/비하"),
        (REPORT5, "낚시/도배성 게시글"),
        (REPORT6, "상업적 광고 및 판매"),
    )
    category = models.CharField(
        choices=REPORT_CATEGORY_CHOICES, max_length=30, blank=False)

    class Meta:
        abstract = True


class PostReport(Report):
    post = models.ForeignKey(
        'Post', related_name='reports', on_delete=models.CASCADE, null=True, blank=False)
    user = models.ForeignKey(
        'users.User', related_name='post_reports', on_delete=models.SET_NULL, null=True, blank=False)


class PostCommentReport(Report):
    comment = models.ForeignKey(
        'PostComment', related_name='reports', on_delete=models.CASCADE, null=True, blank=False)
    user = models.ForeignKey(
        'users.User', related_name='post_comment_reports', on_delete=models.SET_NULL, null=True, blank=False)
