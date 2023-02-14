from django.urls import path
from .views import StoryLikeApi, StoryListApi, StoryDetailApi, StoryCommentListApi, StoryCommentCreateApi, StoryCommentUpdateApi, StoryCommentDeleteApi, GoToMapApi

urlpatterns = [
     path('<int:story_id>/like/', StoryLikeApi.as_view(), name='story_like'),
     path('list/', StoryListApi.as_view(), name='story_list'),
     path('detail/<int:story_id>/', StoryDetailApi.as_view(), name='story_detail'),
     path('comment_list/', StoryCommentListApi.as_view(), name='story_comment_list'),
     path('comment/create/', StoryCommentCreateApi.as_view(), name='comment_create'),
     path('comment/update/<int:story_comment_id>/', StoryCommentUpdateApi.as_view(), name='comment_update'),
     path('comment/delete/<int:story_comment_id>/', StoryCommentDeleteApi.as_view(), name='comment_delete'),
     path('go_to_map/<int:story_id>/', GoToMapApi.as_view(), name='go_to_map'),
]