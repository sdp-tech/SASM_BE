from django.db import models
from django.conf import settings
from core import models as core_models
# Create your models here.

class Photo(core_models.TimeStampedModel):
    """Photo Model Definition"""

    caption = models.CharField(max_length=80)
    file = models.ImageField()
    story = models.ForeignKey("Story", on_delete=models.CASCADE)

    def __str__(self):
        return self.caption

class Story(core_models.TimeStampedModel):
    """Room Model Definition"""

    title = models.CharField(max_length=140)
    description = models.TextField()
    address = models.ForeignKey("places.Place", related_name = 'story', on_delete=models.CASCADE)
    writer = models.ForeignKey("users.User", related_name = 'story', on_delete=models.CASCADE)
    like_user_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="like_post_set"
    )
    like_count = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.title
    class Meta:
        ordering = ["-id"]

class Comment(core_models.TimeStampedModel):
    """Place Model Definition"""
    content = models.TextField()
    writer = models.ForeignKey('users.User', related_name = 'comment', on_delete=models.CASCADE)
    post = models.ForeignKey('stories.Story',related_name = 'comment', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.writer
    
    class Meta:
        ordering = ["-id"]


