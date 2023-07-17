from django.urls import path
from .views import places_view, stories_views, user_following, curations_views, user_info_views, forest_views

urlpatterns = [
     path('follow/', user_following.UserDoUndoFollowApi.as_view(),
          name='user_do_undo_follow'),
     path('following/', user_following.UserFollowingListApi.as_view(),
          name='user_following_list'),
     path('follower/', user_following.UserFollowerListApi.as_view(),
          name='user_follower_list'),
     path('mypick_story/', stories_views.UserStoryListGetApi.as_view(), 
          name='story_edit'),
     path('story_like/', stories_views.UserStoryLikeApi.as_view(), 
          name='story_edit_like'),
     path('my_story/', stories_views.UserCreatedStoryApi.as_view(),
          name='my_story'),
     path('my_curation/', curations_views.MyCurationListApi.as_view(),
         name='my_curation'),
     path('my_liked_curation/', curations_views.MyLikedCurationListApi.as_view(),
         name='my_liked_curation'),
     path('mypick_forest/', forest_views.UserForestListApi.as_view(),
          name='forest_edit'),
     path('my_forest/', forest_views.UserCreateForestApi.as_view(),
          name='my_forest'),
     path('forest_like/', forest_views.UserForestLikeApi.as_view(),
          name='forest_edit_like'),
     path('me/', user_info_views.UserGetApi.as_view(), name='me'),
     path('me/update/', user_info_views.UserUpdateApi.as_view(), name='me_update'),
     path('my_reviewed_place/',places_view.UserReviewedPlaceGetApi.as_view(),
          name='user_reviewed_place'),
     path('myplace_search/',places_view.MyPlaceSearchApi.as_view(), name = 'myplace_search')
]
