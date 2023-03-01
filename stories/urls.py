from django.urls import path
from .views import StoryLikeApi

urlpatterns = [
     path('story_like/', StoryLikeApi.as_view(), name='story_like'),
]
