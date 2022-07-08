from django.db import models
from django.conf import settings
from core import models as core_models
# Create your models here.

class Photo(core_models.TimeStampedModel):
    """Photo Model Definition"""

    caption = models.CharField(max_length=80)
    file = models.ImageField(upload_to='story/%Y%m%d/')
    paragraph = models.ForeignKey("Paragraph", on_delete=models.CASCADE)

    def __str__(self):
        return self.caption

class Story(core_models.TimeStampedModel):
    """Room Model Definition"""

    title = models.CharField(max_length=200)
    story_review = models.CharField(max_length=200)
    address = models.OneToOneField("places.Place", related_name = 'story', on_delete=models.CASCADE)
    story_like_cnt = models.PositiveIntegerField(default=0)
    story_likeuser_set = models.ManyToManyField("users.User",related_name = 'StoryLikeUser',blank=True)
    short_cur = models.TextField(max_length=500)
    tag = models.CharField(max_length=100)

    def __str__(self):
        return self.title
    

class Paragraph(core_models.TimeStampedModel):
    """Paragraph Model Definition"""
    subtitle = models.CharField(max_length=200)
    content = models.TextField()
    post = models.ForeignKey('stories.Story',related_name = 'paragraph', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.subtitle
    
    class Meta:
        ordering = ["-id"]


