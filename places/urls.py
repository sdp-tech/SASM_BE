from django.urls import path
from .views import PlaceDetailView, PlaceLikeView, PlaceListView, MapMarkerView, PlaceReviewView

urlpatterns =[
    #path('save_place/', save_place_db),
    path('map_info/', MapMarkerView.as_view({'get': 'get'}), name="map_info"),
    path('place_detail/',PlaceDetailView.as_view({'get': 'get'}),name="place_detail"),
    path('place_search/',PlaceListView.as_view({'get':'get'}), name='place_search'),
    path('place_like/',PlaceLikeView.as_view({'post':'post'}), name='place_like'),
    path('place_like_user/<int:pk>/',PlaceLikeView.as_view({'get':'get'}), name='place_like'),
    path('place_review/',PlaceReviewView.as_view({'post':'save_review'})),
]
