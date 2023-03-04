from django.urls import path
from .views import StoryCommentUpdateApi

urlpatterns = [
    path('comments/update/<int:story_comment_id>/', StoryCommentUpdateApi.as_view(), name='comments_update'),
]
