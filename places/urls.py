from .views import place_like
from django.urls import path

urlpatterns =[
    path('place_like/<int:id>/', place_like, name="place_like"),
]
