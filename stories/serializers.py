from django.contrib.auth import get_user_model
from rest_framework import serializers
from stories.models import Story
from users.models import User
from places.models import Place

# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Place
#         fields = [
#             'vegan_category',
#             'tumblur_category',
#             'reusable_con_category',
#             'pet_category',
#         ]

class StoryDetailSerializer(serializers.ModelSerializer):
    story_like = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    #onetoonefield에서는 이렇게 참조해와야한다. story의 변수명으로.
    #address = CategorySerializer(required=True)
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
            'views',
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
        result = []
        vegan = place.vegan_category
        if vegan != '':
            result.append(vegan)
        tumblur = place.tumblur_category
        if tumblur == True:
            tumblur = '텀블러 사용 가능'
            result.append(tumblur)
        reusable = place.reusable_con_category
        if reusable == True:
            reusable = '용기내 가능'
            result.append(reusable)
        pet = place.pet_category
        if pet == True:
            pet = '반려동물 출입 가능'
            result.append(pet)
        cnt = len(result)
        ret_result = ""
        for i in range(cnt):
            if i == cnt - 1:
                ret_result = ret_result + result[i]
            else:
                ret_result = ret_result + result[i] + ', '
        return ret_result
    
    def get_place_name(self, obj):
        '''
            스토리에 매핑되는 장소 이름을 알려 주기 위한 함수
        '''        
        story = Story.objects.get(id=obj.id)
        place = story.address
        return place.place_name
        
class StoryListSerializer(serializers.ModelSerializer):
    place_name = serializers.SerializerMethodField()
    story_like = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    semi_category = serializers.SerializerMethodField()
    class Meta:
        model = Story
        fields = [
            'id',
            'title',
            'preview',
            'place_name',
            'story_like',
            'category',
            'semi_category',
            'views',
            ]
    def get_place_name(self, obj):
        '''
            스토리에 매핑되는 장소 이름을 알려 주기 위한 함수
        '''        
        story = Story.objects.get(id=obj.id)
        place = story.address
        return place.place_name
    
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
        result = []
        vegan = place.vegan_category
        if vegan != '':
            result.append(vegan)
        tumblur = place.tumblur_category
        if tumblur == True:
            tumblur = '텀블러 사용 가능'
            result.append(tumblur)
        reusable = place.reusable_con_category
        if reusable == True:
            reusable = '용기내 가능'
            result.append(reusable)
        pet = place.pet_category
        if pet == True:
            pet = '반려동물 출입 가능'
            result.append(pet)
        cnt = len(result)
        ret_result = ""
        for i in range(cnt):
            if i == cnt - 1:
                ret_result = ret_result + result[i]
            else:
                ret_result = ret_result + result[i] + ', '
        return ret_result