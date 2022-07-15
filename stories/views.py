from django.shortcuts import render
from stories import models as story_models
from .serializers import StorySerializer
from rest_framework import viewsets

# Create your views here.
class StoryViewSet(viewsets.ModelViewSet):
    queryset = story_models.Story.objects.all()
    serializer_class = StorySerializer

