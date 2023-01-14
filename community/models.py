from django.db import models
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

    # def clean(self):
    #     self.content = self.content.replace("\r\n", "")


class PostHashtag(TimeStampedModel):
    name = models.CharField(max_length=10)
    post = models.ForeignKey(
        'Post', related_name='hashtags', on_delete=models.CASCADE, null=False, blank=False)


def get_upload_path(instance, filename):
    return 'posts/img/{}'.format(filename)


class PostPhoto(TimeStampedModel):
    image = models.ImageField(
        upload_to=get_upload_path, default='post_image.png')
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
    category = models.CharField(choices=REPORT_CATEGORY_CHOICES, max_length=30, blank=False)

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