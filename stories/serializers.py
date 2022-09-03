from django.contrib.auth import get_user_model
from rest_framework import serializers
from stories.models import Story
from users.models import User
from places.models import Place

class StoryDetailSerializer(serializers.ModelSerializer):
    story_like = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    semi_category = serializers.SerializerMethodField()
    place_name = serializers.SerializerMethodField()
    class Meta:
        model = Story
        fields = [
            'id',
            'title',
            'story_review',
            'tag',
            'story_url',
            'story_like',
            'category',
            'semi_category',
            'place_name',
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
    def get_category(self, obj):
        '''
            스토리의 category를 알려 주기 위한 함수
        '''
        story = Story.objects.get(id=obj.id)
        place = story.address
        return place.category
    
    def get_semi_category(self, obj):
        '''
            스토리의 세부 category를 알려 주기 위한 함수
        '''
        place = Story.objects.get(id=obj.id).address
        vegan = place.vegan_category
        tumblur = place.tumblur_category
        reusable = place.reusable_con_category
        pet = place.pet_category
        return {vegan, tumblur, reusable, pet}
    
    def get_place_name(self, obj):
        '''
            스토리에 매핑되는 장소 이름을 알려 주기 위한 함수
        '''        
        story = Story.objects.get(id=obj.id)
        place = story.address
        return place
        
class StoryListSerializer(serializers.ModelSerializer):
    story_like = serializers.SerializerMethodField()
    place_name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    semi_category = serializers.SerializerMethodField()
    class Meta:
        model = Story
        fields = [
            'id',
            'title',
            'story_review',
            'preview',
            'story_like',
            'place_name',
            'place_category',
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
    def get_place_name(self, obj):
        '''
            스토리에 매핑되는 장소 이름을 알려 주기 위한 함수
        '''        
        story = Story.objects.get(id=obj.id)
        place = story.address
        return place
    
    def get_category(self, obj):
        '''
            스토리의 category를 알려 주기 위한 함수
        '''
        story = Story.objects.get(id=obj.id)
        place = story.address
        return place.category
    
    def get_semi_category(self, obj):
        '''
            스토리의 세부 category를 알려 주기 위한 함수
        '''
        place = Story.objects.get(id=obj.id).address
        vegan = place.vegan_category
        tumblur = place.tumblur_category
        reusable = place.reusable_con_category
        pet = place.pet_category
        return {vegan, tumblur, reusable, pet}