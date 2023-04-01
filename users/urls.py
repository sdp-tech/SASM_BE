from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import base_view, email_auth, login_google, login_kakao, login_naver, pw_change, views
app_name = "users"

urlpatterns = [
    path("signup/", base_view.SignupView.as_view()),
    path("me/", base_view.MeView.as_view()),
    path("<int:pk>/", base_view.user_detail),
    # path('login/',base_view.LoginView.as_view(),name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 위 url에 refresh token 넣어서 POST 보내면 access token 갱신 가능
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # path('logout/', base_view.LogoutView.as_view(),name='logout'),
    # path('findid/',base_view.findemail),
    # path('rep_check/',base_view.rep_check),
    path('kakao/callback/', login_kakao.kakao_callback, name='kakao_callback'),
    path('kakao/login/finish/', login_kakao.KakaoLogin.as_view(),
         name='kakao_login_todjango'),
    path('google/callback/', login_google.google_callback, name='google_callback'),
    path('naver/callback/', login_naver.naver_callback, name='naver_callback'),
    path('activate/<str:uid>/<str:token>',
         email_auth.UserActivateView.as_view(), name='activate'),
    # path('find_pw/',pw_change.PwResetEmailSendView.as_view()),
    # path('pwchangeemail/',pw_change.PasswordChangeView.as_view({'get' : 'get'}),name ='pwchange'),
    # path('pwchange/',pw_change.PasswordChangeView.as_view({'post' : 'post'}),name ='pwchange'),
    # path('like_place/',base_view.UserPlaceLikeView.as_view({'get': 'get'}),name='like_place'),
    # path('like_story/',base_view.UserStoryLikeView.as_view({'get': 'get'}),name='like_story'),
    # path('putme/',views.UserUpdateApi.as_view(), name="user_update"),
    # path('me/',views.UserGetApi.as_view()),
    path('login/', views.UserLoginApi.as_view(), name='login'),
    path('logout/', views.UserLogoutApi.as_view(), name='logout'),
    path('findid/', views.EmailCheckApi.as_view(), name='email_check'),
    path('rep_check/', views.RepCheckApi.as_view(), name='rep_check'),
    path('like_place/', views.UserPlaceLikeApi.as_view(), name='like_place'),
    path('like_story/', views.UserStoryLikeApi.as_view(), name='like_story'),
    path('find_pw/', views.PasswordResetSendEmailApi.as_view(),
         name='pw_change_email'),
    path('pw_reset/', views.PasswordResetApi.as_view(), name='pw_reset'),
    path('pw_change/', views.PasswordChangeApi.as_view(), name='pw_change'),
]
