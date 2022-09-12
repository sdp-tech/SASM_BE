from .views import StoryDetailView, StoryLikeView, StoryListView, GoToMapView
from django.urls import path

urlpatterns =[
    path('story_like/', StoryLikeView.as_view({'post':'post'}), name="story_like"),
    path('story_detail/', StoryDetailView.as_view(), name='story_detail'),
    path('story_search/', StoryListView.as_view({'get': 'get'}), name='story_search'),
    path('go_to_map/', GoToMapView.as_view({'get':'get'}), name='go_to_map'),
]
