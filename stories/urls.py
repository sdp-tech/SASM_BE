from django.urls import path
from .views import StoryListApi, StoryDetailView, StoryLikeApi, StoryListView, GoToMapView, StoryCommentView

urlpatterns = [
     path('story_search/', StoryListApi.as_view(), name='story_search'),
     path('story_like/', StoryLikeApi.as_view(), name='story_like'),
     path('story_detail/', StoryDetailView.as_view(), name='story_detail'),
     path('recommend_story/',
          StoryListView.as_view({'get': 'recommend_story'}), name='story_recommend'),
     path('go_to_map/', GoToMapView.as_view({'get': 'get'}), name='go_to_map'),
     path('comments/',
          StoryCommentView.as_view({'get': 'list', 'post': 'create'}), name='story_comments'),
     path('comments/<int:pk>/',
          StoryCommentView.as_view({'get': 'retrieve', 'patch': 'update', 'delete': 'destroy'}), name='story_comment'),
]