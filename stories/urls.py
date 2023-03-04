from django.urls import path
from .views import StoryCommentDeleteApi

urlpatterns = [
     path('comments/delete/<int:story_comment_id>/', StoryCommentDeleteApi.as_view(), name='comments_delete'),
]
