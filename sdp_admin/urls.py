from django.urls import path
from .views.stories_views import StoryViewSet
from .views.places_views import PlaceViewSet, SNSTypeViewSet, PlacesPhotoViewSet, SNSUrlViewSet
from .views.voc_views import VocViewSet

app_name = 'sdp_admin'

urlpatterns = [
    path('places/save_place/',
         PlaceViewSet.as_view({'post': 'save_place'}), name='save_place'),
    path('places/update_place/',
         PlaceViewSet.as_view({'put': 'update_place'}), name='update_place'),
    path('places/', PlaceViewSet.as_view({'get': 'list'}), name='place_list'),
    path('places/<int:pk>/',
         PlaceViewSet.as_view({'get': 'retrieve'}), name='placedetail'),
    path('places/check_name_overlap/',
         PlaceViewSet.as_view({'get': 'check_name_overlap'}), name='checkoverlap'),
    path('placephoto/<int:pk>/',
         PlacesPhotoViewSet.as_view({'get': 'get'}), name='placephoto'),
    path('snsurl/<int:pk>/',
         SNSUrlViewSet.as_view({'get': 'get'}), name='snsurl'),
    path('snstypes/',
         SNSTypeViewSet.as_view({'get': 'list'}), name='snstype_list'),
    path('stories/photos/',
         StoryViewSet.as_view({'post': 'photos'}), name='story_photo'),
    path('stories/<int:pk>/',
         StoryViewSet.as_view({'get': 'retrieve', 'put': 'update'}), name='storydetail'),
    path('stories/',
         StoryViewSet.as_view({'post': 'create'}), name='create_story'),
    path('voc/', VocViewSet.as_view({'post': 'create'}), name="create_voc"),
    path('voc/<int:pk>/',
         VocViewSet.as_view({'get': 'retrieve'}), name="get_voc"),
    path('voc/list/', VocViewSet.as_view({'get': 'list'}), name="list_voc"),
]
