from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path,include
app_name = "users"

router = DefaultRouter()
router.register("user", views.UsersViewSet)
urlpatterns = [
    path('api/',include(router.urls)),
]