from django.contrib.auth import get_user_model
from rest_framework import serializers
from stories.models import Story, StoryPhoto
from users.models import User
from places.models import Place


class StorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        ordering = ['-id']
        fields = [
            'id',
            'title',
            'story_review',
            'address',
            'tag',
            'preview',
            'rep_pic',
            'html_content',
        ]


class StoryPhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = StoryPhoto
        fields = [
            'caption',
            'image',
        ]
