from django.contrib.auth.models import AbstractUser, AbstractBaseUser, BaseUserManager
from django.db import models
from django.conf import settings
from django.contrib.auth.models import UserManager, PermissionsMixin
from PIL import Image
from PIL import ExifTags
from io import BytesIO
from django.core.files import File

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """custom user model"""
    username = None
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
    profile_image = models.ImageField(upload_to='profile/%Y%m%d/', blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    

    def __str__(self):
        return self.email

#    def save(self, *args, **kwargs):
#        if self.profile_image:
#            pilImage = Image.open(BytesIO(self.profile_image.read()))
#            try:
#                for orientation in ExifTags.TAGS.keys():
#                    if ExifTags.TAGS[orientation] == 'Orientation':
#                        break
#                exif = dict(pilImage._gettextif().items())
#
#                if exif[orientation] == 3:
#                    pilImage = pilImage.rotate(180, expand=True)
#                elif exif[orientation] == 6:
#                    pilImage = pilImage.rotate(270, expand=True)
#                elif exif[orientation] == 8:
#                    pilImage = pilImage.rotate(90, expand=True)
#
#                output = BytesIO()
#                pilImage.save(output, format='JPEG', quality=100)
#                output.seek(0)
#                self.profile_image = File(output, self.profile_image.name)
#            except:
#                pass
#        return super(User, self).save(*args, **kwargs)    

