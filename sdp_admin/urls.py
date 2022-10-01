from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.places_views import PlaceViewSet
from .views.stories_views import StoryViewSet

app_name = 'sdp_admin'

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename="stories")
router.register(r'places', PlaceViewSet, basename="places")


urlpatterns = [
    path('', include(router.urls)),
]


urlpatterns = format_suffix_patterns(urlpatterns)

