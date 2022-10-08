from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.stories_views import StoryViewSet
from .views.places_views import PlacesViewSet, SNSTypeViewSet

app_name = 'sdp_admin'

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename="stories")
router.register(r'places', PlacesViewSet, basename="places")


urlpatterns = [
    path('', include(router.urls)),
    path('snstype/', SNSTypeViewSet.as_view({'get':'get'})),
]

