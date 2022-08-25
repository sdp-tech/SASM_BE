from .views import base_view, email_auth, login_google, login_kakao, login_naver, pw_change
from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView
app_name = "users"

urlpatterns = [
    path("signup/",base_view.SignupView.as_view()),
    path("me/",base_view.MeView.as_view()),
    path("<int:pk>/",base_view.user_detail),
    path('login/',base_view.LoginView.as_view()),
    path('login/refresh/', TokenRefreshView.as_view()), 
    # 위 url에 refresh token 넣어서 POST 보내면 access token 갱신 가능
    path('findid/',base_view.findemail),
    path('rep_check/',base_view.rep_check),
    path('kakao/login/',login_kakao.kakao_login,name='kakao_login'),
    path('kakao/callback/',login_kakao.kakao_callback,name ='kakao_callback'),
    path('kakao/login/finish/',login_kakao.KakaoLogin.as_view(),name='kakao_login_todjango'),
    path('vgoogle/login/',login_google.google_login,name='google_login'),
    path('google/callback/',login_google.google_callback,name='google_callback'),
    path('google/login/finish/',login_google.GoogleLogin.as_view(),name='google_login_todjango'),
    path('naver/login/',login_naver.naver_login,name='naver_login'),
    path('naver/callback/',login_naver.naver_callback,name='naver_callback'),
    path('naver/login/finish/',login_naver.NaverLogin.as_view(),name='naver_login_todjango'),
    path('activate/<str:uid>/<str:token>',email_auth.UserActivateView.as_view(),name ='activate'),
    path('find_pw/',pw_change.PwResetEmailSendView.as_view()),
    path('pwchange/<str:uid>/<str:token>',pw_change.PasswordChangeView.as_view(),name ='pwchange'),
    path('like_place/',base_view.UserLikeView.as_view(),name='like_place'),
]