from django.db import models
from core import models as core_models

# Create your models here.
class Voc(core_models.TimeStampedModel):
    """voc model"""
    content = models.TextField(max_length=1000)
    customer = models.ForeignKey("users.User", on_delete=models.CASCADE)

    def __str__(self):
        return self.customer.email