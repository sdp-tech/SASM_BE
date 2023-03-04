from django.urls import path
from .views import GoToMapApi

urlpatterns = [
     path('go_to_map/', GoToMapApi.as_view(), name='go_to_map'),
]
