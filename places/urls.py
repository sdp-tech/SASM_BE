from django.urls import path
from .views.get_place_info import PlaceDetailView, PlaceListView, MapMarkerApi
from .views.like_place import PlaceLikeView
from .views.place_review_views import PlaceReviewView, PlaceVisitorReviewCreateApi, PlaceVisitorReviewUpdateApi, PlaceVisitorReviewListApi

urlpatterns = [
    path('map_info/', MapMarkerApi.as_view(), name="map_info"),
    path('place_detail/',
         PlaceDetailView.as_view({'get': 'get'}), name="place_detail"),
    path('place_search/',
         PlaceListView.as_view({'get': 'get'}), name='place_search'),
    path('place_like/',
         PlaceLikeView.as_view({'post': 'post'}), name='place_like'),
    path('place_like_user/<int:pk>/',
         PlaceLikeView.as_view({'get': 'get'}), name='place_like'),
    path('place_review/',
         PlaceReviewView.as_view({'get': 'list', 'post': 'save_review'})),
    path('place_review/<int:pk>/',
         PlaceReviewView.as_view({'get': 'retrieve', 'delete': 'destroy', 'put': 'put'})),
    path('place_review/create/', PlaceVisitorReviewCreateApi.as_view()),
    path('place_review/<int:place_review_id>/update',
         PlaceVisitorReviewUpdateApi.as_view()),
    path('place_reviews/', PlaceVisitorReviewListApi.as_view())
]
