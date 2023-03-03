from django.urls import path
from .views import StoryDetailApi

urlpatterns = [
     path('story_detail/', StoryDetailApi.as_view(), name='story_detail'),
]
