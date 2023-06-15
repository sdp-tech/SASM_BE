from django.contrib import admin
from . import models


@admin.register(models.Category)
class Category(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.SemiCategory)
class SemiCategory(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.Forest)
class Forest(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.ForestHashtag)
class ForestHashtag(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.ForestPhoto)
class ForestPhoto(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.ForestReport)
class ForestReport(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.ForestComment)
class ForestComment(admin.ModelAdmin):

    """ """

    pass
