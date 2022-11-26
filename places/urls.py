from django.urls import path
from .views.get_place_info import PlaceDetailView, PlaceListView, MapMarkerView
from .views.like_place import PlaceLikeView
# from .views.save_place_excel import save_place_db
urlpatterns =[
    # path('save_place/', save_place_db),
    path('map_info/', MapMarkerView.as_view({'get': 'get'}), name="map_info"),
    path('place_detail/',PlaceDetailView.as_view({'get': 'get'}),name="place_detail"),
    path('place_search/',PlaceListView.as_view({'get':'get'}), name='place_search'),
    path('place_like/',PlaceLikeView.as_view({'post':'post'}), name='place_like'),
    path('place_like_user/<int:pk>/',PlaceLikeView.as_view({'get':'get'}), name='place_like'),
]
