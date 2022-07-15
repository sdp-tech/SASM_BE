from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import StoryViewSet, story_like

urlpatterns =[
    path('story_like/<int:id>/', story_like, name="story_like"),
]
