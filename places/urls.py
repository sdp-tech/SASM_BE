from .views import place_like, save_place_db
from django.urls import path

urlpatterns =[
    path('place_like/<int:id>/', place_like, name="place_like"),
    path('save_place/', save_place_db),
]
