from django.urls import path
from .views import StoryRecommendApi

urlpatterns = [
     path('recommend_story/', StoryRecommendApi.as_view(), name='story_recommend'),
]
