from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("signup/", views.SignupView.as_view()),
    path("me/", views.MeView.as_view()),
    path("<int:pk>/", views.user_detail),
    path('login/', views.Login),
    path('activate/<str:uid>/<str:token>',views.UserActivateView.as_view(), name ='activate'),
    path('find_pw/',views.PwResetEmailSendView.as_view()),
    path('pwchange/<str:uid>/<str:token>',views.PasswordChangeView.as_view(), name ='pwchange'),
    path('findid/',views.findemail),
]