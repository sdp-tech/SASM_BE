from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import base_view, email_auth, login_google, login_kakao, login_naver, views
app_name = "users"

urlpatterns = [
    path("signup/", views.SignUpApi.as_view()),
    path("me/", base_view.MeView.as_view()),
    #     path("<int:pk>/", base_view.user_detail),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 위 url에 refresh token 넣어서 POST 보내면 access token 갱신 가능
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('kakao/callback/', login_kakao.kakao_callback, name='kakao_callback'),
    path('google/callback/', login_google.google_callback, name='google_callback'),
    path('naver/callback/', login_naver.naver_callback, name='naver_callback'),
    path('activate/<str:uid>/<str:token>',
         email_auth.UserActivateView.as_view(), name='activate'),
    path('login/', views.UserLoginApi.as_view(), name='login'),
    path('logout/', views.UserLogoutApi.as_view(), name='logout'),
    path('findid/', views.EmailCheckApi.as_view(), name='email_check'),
    path('rep_check/', views.RepCheckApi.as_view(), name='rep_check'),
    path('like_place/', views.UserPlaceLikeApi.as_view(), name='like_place'),
    path('like_story/', views.UserStoryLikeApi.as_view(), name='like_story'),
    path('my_story/', views.UserStoryGetApi.as_view(), name='my_story'),
    path('my_story_comment/', views.UserStoryGetByCommentApi.as_view(),
         name='my_story_comment'),
    path('find_pw/', views.PasswordResetSendEmailApi.as_view(),
         name='pw_change_email'),
    path('pw_reset/', views.PasswordResetApi.as_view(), name='pw_reset'),
    path('pw_change/', views.PasswordChangeApi.as_view(), name='pw_change'),
    path('follow/', views.UserDoUndoFollowApi.as_view(),
         name='user_do_undo_follow'),
    path('following/', views.UserFollowingListApi.as_view(),
         name='user_following_list'),
    path('follower/', views.UserFollowerListApi.as_view(),
         name='user_follower_list'),
]
