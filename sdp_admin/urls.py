from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.stories_views import StoryViewSet

app_name = 'sdp_admin'

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename="stories")


urlpatterns = [
    path('', include(router.urls)),
]
