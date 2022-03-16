from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import StoryViewSet

router = DefaultRouter()
router.register('story',StoryViewSet)
urlpatterns =[
    path('api/',include(router.urls)),
]
