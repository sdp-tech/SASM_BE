from django.contrib.auth import get_user_model
from rest_framework import serializers
from stories import models as story_models

class StorySerializer(serializers.ModelSerializer):
   
    class Meta:
        model = story_models.Story
        fields = [
            'id',
            'title',
            'story_review',
            'address',
            'story_like_cnt',
            'story_likeuser_set',
            'tag',
            'preview',
            'views',
            ]