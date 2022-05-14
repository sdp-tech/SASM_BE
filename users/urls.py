from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path("signup/", views.SignupView.as_view(), name="login"),
    path("me/", views.MeView.as_view()),
    path("<int:pk>/", views.user_detail),
]