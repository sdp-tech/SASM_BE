from django.urls import path
from .views import stories_views
from .views import places_views

app_name = 'sdp_admin'

urlpatterns = [
    # stories_views
    path('stories/', stories_views.stories_list),
    path('stories/<int:pk>', stories_views.stories_detail),
    # places_views
    path('places/', places_views.places_list),
    path('places/<int:pk>', places_views.places_detail),
]