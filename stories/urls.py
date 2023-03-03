from django.urls import path
from .views import StoryCommentListApi

urlpatterns = [
     path('comments/', StoryCommentListApi.as_view(), name='story_comments'),
]
