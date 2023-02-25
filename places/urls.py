from django.urls import path
from .views.get_place_info import PlaceListApi, PlaceDetailApi, MapMarkerApi
from .views.like_place import PlaceLikeApi
from .views.place_review_views import PlaceReviewView, PlaceReviewListApi, PlaceReviewCreateApi, PlaceReviewUpdateApi, PlaceReviewDeleteApi
#from .views.save_place_excel import save_place_db

urlpatterns =[
    #path('save_place/', save_place_db),
    path('map_info/', MapMarkerApi.as_view(), name='map_info'),
    path('place_detail/',PlaceDetailApi.as_view(),name="place_detail"),
    path('place_search/',PlaceListApi.as_view(), name='place_search'),
    path('place_like/',PlaceLikeApi.as_view(), name='place_like'),
    path('place_like_user/<int:pk>/',PlaceLikeApi.as_view(), name='place_like'),
    path('place_review/',PlaceReviewListApi.as_view()),
    path('place_review/create/',PlaceReviewCreateApi.as_view()), # TODO: sync with FE
    path('place_review/<int:pk>/update/',PlaceReviewUpdateApi.as_view()), # TODO: sync with FE
    path('place_review/<int:pk>/delete/',PlaceReviewDeleteApi.as_view()), # TODO: sync with FE
    path('place_review/<int:pk>/',PlaceReviewView.as_view({'get':'retrieve','delete':'destroy','put':'put'})),
]
