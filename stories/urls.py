from django.urls import path
from .views import StoryLikeApi, StoryListApi, StoryRecommendApi, StoryDetailApi, StoryCommentListApi, StoryCommentCreateApi, StoryCommentUpdateApi, StoryCommentDeleteApi, GoToMapApi

urlpatterns = [
     path('story_like/', StoryLikeApi.as_view(), name='story_like'),
     path('story_search/', StoryListApi.as_view(), name='story_search'),
     path('story_detail/', StoryDetailApi.as_view(), name='story_detail'),
     path('comments/', StoryCommentListApi.as_view(), name='story_comments'),
     path('comments/create/', StoryCommentCreateApi.as_view(), name='comments_create'),
     path('comments/update/<int:story_comment_id>/', StoryCommentUpdateApi.as_view(), name='comments_update'),
     path('comments/delete/<int:story_comment_id>/', StoryCommentDeleteApi.as_view(), name='comments_delete'),
     path('go_to_map/', GoToMapApi.as_view(), name='go_to_map'),
     path('recommend_story/', StoryRecommendApi.as_view(), name='story_recommend'),
]