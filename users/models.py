from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
# Create your models here.
class User(AbstractUser):
    """custom user model"""

    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_OTHER = "other"
    GENDER_CHOICES = (
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
        (GENDER_OTHER, "Other"),
    )
    gender = models.CharField(choices=GENDER_CHOICES, max_length=10, blank=True)
    nickname = models.CharField(max_length=20, blank=True)
    birthdate = models.DateField(blank=True, null=True)
    email = models.EmailField(max_length=64,unique=True)
    address = models.CharField(max_length=100, blank=True)