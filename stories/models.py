from core import models as core_models
from django.db import models

# Create your models here.


def get_upload_path(instance, filename):
    return 'stories/img/{}'.format(filename)


class StoryPhoto(core_models.TimeStampedModel):
    """Photo Model Definition"""

    caption = models.CharField(max_length=80)
    image = models.ImageField(
        upload_to=get_upload_path, default='story_image.png')

    def __str__(self):
        return self.caption


class Story(core_models.TimeStampedModel):
    """Room Model Definition"""

    title = models.CharField(max_length=200)
    story_review = models.CharField(max_length=200)
    address = models.OneToOneField("places.Place", on_delete=models.CASCADE)
    story_like_cnt = models.PositiveIntegerField(default=0)
    story_likeuser_set = models.ManyToManyField(
        "users.User", related_name='StoryLikeUser', blank=True)
    tag = models.CharField(max_length=100)
    preview = models.CharField(max_length=150, blank=True)
    views = models.PositiveIntegerField(default=0, verbose_name='조회수')
    rep_pic = models.URLField(max_length=300, blank=True)
    html_content = models.TextField(max_length=50000)

    def clean(self):
        self.html_content = self.html_content.replace("\r\n", "")

    def __str__(self):
        return self.title
