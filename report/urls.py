from django.urls import path
from .views import ReportCreateApi
urlpatterns = [
    path('create/', ReportCreateApi.as_view(), name="report_create"),
]
