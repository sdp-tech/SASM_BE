from django.contrib.auth import get_user_model
from rest_framework import serializers
from stories import models as story_models
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id","username","email","gender","nickname","birthdate"]

class StorySerializer(serializers.ModelSerializer):
    writer = AuthorSerializer(read_only=True)
    class Meta:
        model = story_models.Story
        fields = [
            'id',
            'writer',
            'title',
            'description',
            'address',
            'created',
            'updated',
            ]

