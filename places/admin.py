from django.contrib import admin
from . import models
# Register your models here.

@admin.register(models.PlacePhoto)
class PhotoAdmin(admin.ModelAdmin):

    """ """

    pass
@admin.register(models.SNSType)
class SNsAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Place)
class PlaceAdmin(admin.ModelAdmin):
    pass

@admin.register(models.SNSUrl)
class PlaceAdmin(admin.ModelAdmin):
    pass