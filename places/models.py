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

class PlaceType(AbstractItem):
    pass

    class Meta:
        verbose_name = "Place Type"

class Photo(core_models.TimeStampedModel):
    """Photo Model Definition"""

    caption = models.CharField(max_length=80)
    file = models.ImageField()
    place = models.ForeignKey("Place", on_delete=models.CASCADE)

    def __str__(self):
        return self.caption

class Place(core_models.TimeStampedModel):
    """Place Model Definition"""

    name = models.CharField(max_length=140)
    description = models.TextField()
    address = models.CharField(max_length=140)
    place_type = models.ManyToManyField("PlaceType", related_name = 'place', blank = True)

    def __str__(self):
        return self.name