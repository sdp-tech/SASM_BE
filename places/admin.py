from django.contrib import admin
from . import models
# Register your models here.
@admin.register(models.PlaceType)
class ItemAdmin(admin.ModelAdmin):
    
    pass

@admin.register(models.Photo)
class PhotoAdmin(admin.ModelAdmin):

    """ """

    pass

@admin.register(models.Place)
class PlaceAdmin(admin.ModelAdmin):
    pass