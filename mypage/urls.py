from django.urls import path
from .views import stories_views

urlpatterns = [
    path('my_story/', stories_views.UserStoryGetApi.as_view(), name='my_story'),
]
