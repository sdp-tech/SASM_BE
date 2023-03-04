from django.urls import path
from .views import StoryCommentCreateApi

urlpatterns = [
     path('comments/create/', StoryCommentCreateApi.as_view(), name='comments_create'),
]
