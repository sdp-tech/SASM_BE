from django.urls import path
from .views import stories_views, user_following

urlpatterns = [
     path('follow/', user_following.UserDoUndoFollowApi.as_view(),
          name='user_do_undo_follow'),
     path('following/', user_following.UserFollowingListApi.as_view(),
          name='user_following_list'),
     path('follower/', user_following.UserFollowerListApi.as_view(),
          name='user_follower_list'),
     path('story_edit/', stories_views.UserStoryListGetApi.as_view(), 
          name='story_edit'),
     path('story_like/', stories_views.UserStoryLikeApi.as_view(), 
          name='story_edit_like'),
     path('my_story/', stories_views.UserCreatedStoryApi.as_view(),
          name='my_story'),
]
