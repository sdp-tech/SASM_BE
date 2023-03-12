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

@admin.register(models.CategoryContent)
class CategoryContentAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PlaceVisitorReviewCategory)
class PlaceVisitorReviewCategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PlaceVisitorReview)
class PlaceVisitorReviewAdmin(admin.ModelAdmin):
    pass

@admin.register(models.PlaceVisitorReviewPhoto)
class PlaceVisitorReviewPhotoAdmin(admin.ModelAdmin):
    pass
