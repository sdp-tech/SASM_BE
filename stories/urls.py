from django.urls import path
from .views import StoryCommentCreateApi

urlpatterns = [
     path('comment/create/', StoryCommentCreateApi.as_view(), name='comment_create'),
]
