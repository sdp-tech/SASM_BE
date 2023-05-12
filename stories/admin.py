from django.contrib import admin
from . import models

# Register your models here.


@admin.register(models.StoryPhoto)
class PhotoAdmin(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.Story)
class StoryAdmin(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.StoryComment)
class StoryCommentAdmin(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.StoryMap)
class StoryMapAdmin(admin.ModelAdmin):

    """ """

    pass
