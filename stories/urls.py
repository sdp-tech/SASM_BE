from django.urls import path
from .views import StoryListApi

urlpatterns = [
     path('story_search/', StoryListApi.as_view(), name='story_search'),
]
