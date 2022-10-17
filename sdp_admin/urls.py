from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.stories_views import StoryViewSet
from .views.places_views import PlaceViewSet, SNSTypeViewSet, PlacesPhotoViewSet,SNSUrlViewSet

app_name = 'sdp_admin'

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename="stories")
router.register(r'places', PlaceViewSet, basename="places")
router.register(r'snstypes', SNSTypeViewSet, basename="snstypes")

urlpatterns = [
    path('', include(router.urls)),
    path('placephoto/<int:pk>/',PlacesPhotoViewSet.as_view({'get':'get'}),name='placephoto'),
    path('snsurl/<int:pk>/',SNSUrlViewSet.as_view({'get':'get'}),name='snsurl'),
]
