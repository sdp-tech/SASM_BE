from django.urls import path
from .views import place_like

urlpatterns =[
    path('place_like/<int:id>/', place_like, name="place_like"),
]
