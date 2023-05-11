from django.db import models
from core import models as core_models
from django.dispatch import receiver


def get_upload_path(instance, filename):
    return 'stories/img/{}'.format(filename)


class StoryPhoto(core_models.TimeStampedModel):
    """Photo Model Definition"""

    story = models.ForeignKey(
        "Story", related_name='photos', on_delete=models.CASCADE, null=True, blank=True)
    caption = models.CharField(max_length=80)
    image = models.ImageField(
        upload_to=get_upload_path, default='story_image.png')

    def __str__(self):
        return self.caption


@receiver(models.signals.post_delete, sender=StoryPhoto)
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.image.delete(save=False)


class Story(core_models.TimeStampedModel):
    """Room Model Definition"""

    title = models.CharField(max_length=200)
    story_review = models.CharField(max_length=200)
    address = models.OneToOneField(
        "places.Place", on_delete=models.CASCADE, null=True, blank=True)
    place = models.ForeignKey(
        "places.Place", on_delete=models.CASCADE, related_name='stories', null=True, blank=True)
    story_like_cnt = models.PositiveIntegerField(default=0)
    story_likeuser_set = models.ManyToManyField(
        "users.User", related_name='StoryLikeUser', blank=True)
    tag = models.CharField(max_length=100)
    preview = models.CharField(max_length=150, blank=True)
    views = models.PositiveIntegerField(default=0, verbose_name='조회수')
    rep_pic = models.ImageField(
        upload_to=get_upload_path, default='story_rep_pic.png')
    html_content = models.TextField(max_length=50000)
    writer = models.ForeignKey(
        'users.User', related_name='stories', on_delete=models.SET_NULL, null=True, blank=False)

    def clean(self):
        self.html_content = self.html_content.replace("\r\n", "")

    def __str__(self):
        return self.title

    def entire_update(self, title, story_review, tag, preview, html_content, rep_pic):
        self.title = title
        self.story_review = story_review
        self.tag = tag
        self.preview = preview
        self.html_content = html_content
        self.rep_pic = rep_pic


class StoryComment(core_models.TimeStampedModel):
    story = models.ForeignKey(
        'Story', related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    # isParent: true일 경우 parent 댓글, false일 경우 child 댓글
    isParent = models.BooleanField(null=False, blank=False, default=True)
    # parent 댓글이 삭제되어도, child 댓글은 유지, parent를 null 설정
    parent = models.ForeignKey(
        'StoryComment', related_name='childs', on_delete=models.SET_NULL, null=True, blank=True)
    # 댓글 writer가 회원 탈퇴해도, 댓글은 유지, writer를 null 설정
    writer = models.ForeignKey(
        'users.User', related_name='story_comments', on_delete=models.SET_NULL, null=True, blank=False)
    # 멘션된 사용자가 회원 탈퇴하더라도, 댓글은 유지, mention을 null 설정
    mention = models.ForeignKey(
        'users.User', related_name='mentioned_story_comments', on_delete=models.SET_NULL, null=True, blank=True)

    # TODO: TimestampedModel 필드와 중복, 삭제 필요
    created_at = models.DateTimeField(auto_now_add=True)
    # TODO: TimestampedModel 필드와 중복, 삭제 필요
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.story.title, str(self.id))


class StoryMap(core_models.TimeStampedModel):
    story = models.ForeignKey(
        "Story", related_name='map_photos', on_delete=models.CASCADE, null=True)
    map = models.ImageField(
        upload_to=get_upload_path, default='story_map_photo.png')


@receiver(models.signals.post_delete, sender=StoryMap)
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.map.delete(save=False)
