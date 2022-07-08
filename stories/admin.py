from django.contrib import admin
from . import models

# Register your models here.
@admin.register(models.Photo)
class PhotoAdmin(admin.ModelAdmin):

    """ """

    pass

@admin.register(models.Story)
class StoryAdmin(admin.ModelAdmin):

    """ """

    pass
@admin.register(models.Paragraph)
class CommentAdmin(admin.ModelAdmin):
    
    pass