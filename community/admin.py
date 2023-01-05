from django.contrib import admin
from . import models


@admin.register(models.Board)
class BoardAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PostHashtag)
class PostHashtagAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PostPhoto)
class PostPhotoAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    pass
