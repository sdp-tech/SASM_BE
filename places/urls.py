from .views import PlaceDetailView,save_place_db, PlaceLikeView, PlaceListView
from django.urls import path

urlpatterns =[
    path('save_place/', save_place_db),
    path('place_detail/<int:pk>/',PlaceDetailView.as_view({'get': 'get'}),name="place_detail"),
    path('place_search/',PlaceListView.as_view({'get':'get'}), name='place_search'),
    path('place_like/',PlaceLikeView.as_view({'post':'post'}), name='place_like'),
    path('place_like_user/<int:pk>/',PlaceLikeView.as_view({'get':'get'}), name='place_like'),
]
