from .views import story_like
from django.urls import path

urlpatterns =[
    path('story_like/<int:id>/', story_like, name="story_like"),
]
