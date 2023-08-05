from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import email_auth, login_google, login_kakao, login_naver, login_apple, views
app_name = "users"

urlpatterns = [
    path("signup/", views.SignUpApi.as_view()),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 위 url에 refresh token 넣어서 POST 보내면 access token 갱신 가능
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('kakao/callback/', login_kakao.kakao_callback, name='kakao_callback'),
    path('google/callback/', login_google.google_callback, name='google_callback'),
    path('naver/callback/', login_naver.naver_callback, name='naver_callback'),
    path('apple/callback/', login_apple.apple_callback, name='apple_callback'),
    path('activate/<str:uid>/<str:token>',
         email_auth.UserActivateView.as_view(), name='activate'),
    path('login/', views.UserLoginApi.as_view(), name='login'),
    path('logout/', views.UserLogoutApi.as_view(), name='logout'),
    path('findid/', views.EmailCheckApi.as_view(), name='email_check'),
    path('rep_check/', views.RepCheckApi.as_view(), name='rep_check'),

    ####### TODO: mypage 이관 후 제거 필요 #######
    path('like_place/', views.UserPlaceLikeApi.as_view(), name='like_place'),
    path('like_story/', views.UserStoryLikeApi.as_view(), name='like_story'),
    path('my_story/', views.UserStoryGetApi.as_view(), name='my_story'),
    path('my_story_comment/', views.UserStoryGetByCommentApi.as_view(),
         name='my_story_comment'),
    ########################################################

    path('find_pw/', views.PasswordResetSendEmailApi.as_view(),
         name='pw_change_email'),  # 비밀번호 reset을 위한 인증 메일을 발송
    path('pw_reset/', views.PasswordResetApi.as_view(),
         name='pw_reset'),  # 인증코드와 새 비밀번호를 받아 비밀번호 reset 수행
    path('pw_change/', views.PasswordChangeApi.as_view(), name='pw_change'),
]
