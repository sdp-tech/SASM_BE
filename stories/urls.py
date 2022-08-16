from .views import StoryDetailView, story_like
from django.urls import path

urlpatterns =[
    path('story_like/<int:id>/', story_like, name="story_like"),
    path('story_detail/<int:id>', StoryDetailView.as_view(), name='story_detail'),
]
