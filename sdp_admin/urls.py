from django.urls import path, include
<<<<<<< HEAD
from rest_framework import urls, renderers
from rest_framework.routers import DefaultRouter
from .views.places_views import PlacesViewSet

app_name = 'sdp_admin'

router = DefaultRouter()
router.register(r'places', PlacesViewSet, basename="places")

urlpatterns = [
    path('', include(router.urls)),
]
=======
from rest_framework.routers import DefaultRouter

from .views.stories_views import StoryViewSet

app_name = 'sdp_admin'

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename="stories")


urlpatterns = [
    path('', include(router.urls)),
]
>>>>>>> 1a1b26c89a8aff5a03dd199467db70ce80cd9432
