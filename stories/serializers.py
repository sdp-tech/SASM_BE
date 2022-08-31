from django.contrib.auth import get_user_model
from rest_framework import serializers
from stories.models import Story
from users.models import User
class StorySerializer(serializers.ModelSerializer):
    story_like = serializers.SerializerMethodField()
    class Meta:
        model = Story
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
            'story_url',
            'story_like',
            ]
    def get_story_like(self,obj):
        '''
        스토리의 좋아요 여부를 알려주기 위한 함수
        '''
        story = Story.objects.get(id=obj.id)
        re_user =  self.context['request'].user.id
        like_id = story.story_likeuser_set.all()
        users = User.objects.filter(id__in=like_id)
        if users.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none'