from django.contrib.auth import get_user_model
from rest_framework import serializers
from stories.models import Story, StoryPhoto, StoryComment
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
    # onetoonefield에서는 이렇게 참조해와야한다. story의 변수명으로.
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
            'story_like',
            'category',
            'semi_category',
            'place_name',
            'views',
            'html_content',
        ]

    def get_story_like(self, obj):
        '''
        스토리의 좋아요 여부를 알려주기 위한 함수
        '''
        re_user = self.context['request'].user.id
        like_id = obj.story_likeuser_set.all()
        users = User.objects.filter(id__in=like_id)
        if users.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none'

    def get_category(self, obj):
        '''
            스토리의 category를 알려 주기 위한 함수
        '''
        place = obj.address
        return place.category

    def get_semi_category(self, obj):
        '''
            스토리의 세부 category를 알려 주기 위한 함수
        '''
        place = obj.address
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
        place = obj.address
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
            'rep_pic',
            'created',
        ]

    def get_place_name(self, obj):
        '''
            스토리에 매핑되는 장소 이름을 알려 주기 위한 함수
        '''
        place = obj.address
        return place.place_name

    def get_story_like(self, obj):
        '''
        스토리의 좋아요 여부를 알려주기 위한 함수
        '''
        re_user = self.context['request'].user.id
        like_id = obj.story_likeuser_set.all()
        users = User.objects.filter(id__in=like_id)
        if users.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none'

    def get_category(self, obj):
        '''
            스토리의 category를 알려 주기 위한 함수
        '''
        place = obj.address
        return place.category

    def get_semi_category(self, obj):
        '''
            스토리의 세부 category를 알려 주기 위한 함수
        '''
        place = obj.address
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


class StoryCommentSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = StoryComment
        ordering = ['id']
        fields = [
            'id',
            'story',
            'content',
            'isParent',
            'parent',
            'writer',
            'mention',
            'nickname',
            'email',
        ]

    def get_nickname(self, obj):
        return obj.writer.nickname

    def get_email(self, obj):
        return obj.writer.email

    def validate(self, data):
        if 'parent' in data:
            parent = data['parent']

            # child comment를 parent로 설정 시 reject
            if parent and not parent.isParent:
                raise serializers.ValidationError(
                    'can not set the child comment as parent comment')
            # parent가 null이 아닌데(자신이 child), isParent가 true인 경우 reject
            if parent is not None and data['isParent']:
                raise serializers.ValidationError(
                    'child comment has isParent value be false')
            # parent가 null인데(자신이 parent), isParent가 false인 경우 reject
            if data['parent'] is None and not data['isParent']:
                raise serializers.ValidationError(
                    'parent comment has isParent value be true')
        return data


class StoryCommentUpdateSerializer(StoryCommentSerializer):
    class Meta:
        model = StoryComment
        ordering = ['id']
        fields = [
            'id',
            'content',
            'mention',
        ]


class StoryCommentCreateSerializer(StoryCommentSerializer):
    class Meta:
        model = StoryComment
        ordering = ['id']
        fields = [
            'id',
            'story',
            'content',
            'isParent',
            'parent',
            'mention',
        ]

    def create(self, validated_data):
        comment = StoryComment(**validated_data)
        comment.writer = self.context['request'].user
        comment.save()

        return comment
