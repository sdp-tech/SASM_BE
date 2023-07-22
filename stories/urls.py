from django.urls import path
from .views import StoryDetailApi, StoryCreateApi, StoryUpdateApi, StoryDeleteApi, StoryRecommendApi, StoryLikeApi, StoryPhotoCreateApi, StoryListApi, GoToMapApi, StoryCommentListApi, StoryCommentLikeApi, StoryCommentCreateApi, StoryCommentUpdateApi, StoryCommentDeleteApi

urlpatterns = [
     path('<int:story_id>/story_like/',
          StoryLikeApi.as_view(), name="story_like"),
     path('story_detail/<int:story_id>/', StoryDetailApi.as_view(), name='story_detail'),
     path('create/', StoryCreateApi.as_view(), name='story_create'),
     path('story_photos/create/',
         StoryPhotoCreateApi.as_view(), name='story_photo'),
     path('<int:story_id>/update/', StoryUpdateApi.as_view(), name='story_update'),
     path('<int:story_id>/delete/', StoryDeleteApi.as_view(), name='story_delete'),
     path('story_search/',
          StoryListApi.as_view(), name='story_search'),
     path('recommend_story/', StoryRecommendApi.as_view(), name='story_recommend'),
     path('go_to_map/', GoToMapApi.as_view(), name='go_to_map'),
     path('comments/', StoryCommentListApi.as_view(), name='story_comments'),
     path('comments/create/', StoryCommentCreateApi.as_view(), name='comments_create'),
     path('comments/update/<int:story_comment_id>/', 
          StoryCommentUpdateApi.as_view(), name='comments_update'),
     path('comments/delete/<int:story_comment_id>/', StoryCommentDeleteApi.as_view(), name='comments_delete'),
     path('<int:story_id>/comments/<int:story_comment_id>/like/',
          StoryCommentLikeApi.as_view(), name='comments_like'),
]
