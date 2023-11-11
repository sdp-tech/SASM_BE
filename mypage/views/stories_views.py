from rest_framework.views import APIView
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from users.serializers import UserSerializer
from users.models import User
from mypage.selectors.stories_selectors import UserStorySelector, UserCreatedStorySelector
from stories.selectors import StoryLikeSelector
from stories.services import StoryCoordinatorService
from stories.permissions import IsWriter
from stories.models import Story

from core.views import get_paginated_response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class UserStoryListGetApi(APIView):
    permission_classes = (IsAuthenticated, )

    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class UserStoryFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        filter = serializers.ListField(required=False)

    class UserStoryOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        place_name = serializers.SerializerMethodField()
        title = serializers.CharField()
        preview = serializers.CharField()
        story_review = serializers.CharField()
        tag = serializers.CharField()
        rep_pic = serializers.CharField()
        extra_pics = serializers.ListField()
        story_like = serializers.SerializerMethodField()
        writer = serializers.CharField()
        nickname = serializers.CharField()
        category = serializers.CharField()

        def get_place_name(self, obj):
            return obj.place.place_name

        def get_story_like(self, obj):
            re_user = self.context['request'].user
            likes = StoryLikeSelector.likes(obj.id, user=re_user)
            return likes
        
    @swagger_auto_schema(
        operation_id='마이페이지 좋아요한 스토리 조회',
        operation_description='''
            마이페이지에서 좋아요한 스토리를 조회합니다. 쿼리 파라미터 : search, filter <br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'preview': '서울숲. 가장 도시적인 단어...(최대 150자)',
                        'story_review': '"모두에게 열려있는 도심 속 가장 자연 친화적인 여가공간"',
                        'tag': '#생명 다양성 #자연 친화 #함께 즐기는',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'extra_pics': ['https://abc.com/2.jpg'],
                        'story_like': True,
                        'writer': 'sdptech@gmail.com',
                        'nickname': 'sdp_official',
                        'category': '식당 및 카페',
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.UserStoryFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = UserStorySelector(user=request.user)
        like_story = selector.list(
            search=filters.get('search', ''),
            filter=filters.get('filter', []),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserStoryOutputSerializer,
            queryset=like_story,
            request=request,
            view=self,
        )


class UserCreatedStoryApi(APIView):
    permission_classes = (IsWriter, )

    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'
        
    class UserCreatedStoryFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        filter = serializers.ListField(required=False)

    class UserCreatedStoryOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        place_name = serializers.SerializerMethodField()
        title = serializers.CharField()
        preview = serializers.CharField()
        story_review = serializers.CharField()
        tag = serializers.CharField()
        rep_pic = serializers.CharField()
        extra_pics = serializers.ListField()
        story_like = serializers.SerializerMethodField()
        writer = serializers.CharField()
        nickname = serializers.CharField()
        category = serializers.CharField()

        def get_place_name(self, obj):
            return obj.place.place_name

        def get_story_like(self, obj):
            re_user = self.context['request'].user
            likes = StoryLikeSelector.likes(obj.id, user=re_user)
            return likes

    @swagger_auto_schema(
        security=[],
        operation_id='사용자가 작성한 스토리 조회',
        operation_description='''
            사용자가 작성한 스토리를 조회합니다. 쿼리 파라미터 : search, filter <br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'preview': '서울숲. 가장 도시적인 단어...(최대 150자)',
                        'story_review': '"모두에게 열려있는 도심 속 가장 자연 친화적인 여가공간"',
                        'tag': '#생명 다양성 #자연 친화 #함께 즐기는',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'extra_pics': ['https://abc.com/2.jpg'],
                        'story_like': True,
                        'writer': 'sdptech@gmail.com',
                        'nickname': 'sdp_official',
                        'category': '식당 및 카페',
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        }
    )
    def get(self, request):
        filters_serializer = self.UserCreatedStoryFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = UserCreatedStorySelector(user=request.user)
        user_story = selector.list(
            search=filters.get('search', ''),
            filter=filters.get('filter', []),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserCreatedStoryOutputSerializer,
            queryset=user_story,
            request=request,
            view=self,
        )

class OtherCreatedStoryApi(APIView):
    permission_classes = (IsWriter, )

    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class OtherCreatedStoryFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        filter = serializers.ListField(required=False)

    class OtherCreatedStoryOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        place_name = serializers.SerializerMethodField()
        title = serializers.CharField()
        preview = serializers.CharField()
        story_review = serializers.CharField()
        tag = serializers.CharField()
        rep_pic = serializers.CharField()
        extra_pics = serializers.ListField()
        story_like = serializers.SerializerMethodField()
        writer = UserSerializer()
        nickname = serializers.CharField()
        category = serializers.CharField()

        def get_place_name(self, obj):
            return obj.place.place_name

        def get_story_like(self, obj):
            request = self.context.get('request')
            if request:
                re_user = request.user
                likes = StoryLikeSelector.likes(obj.id, user=re_user)
                return likes

    @swagger_auto_schema(
        security=[],
        operation_id='다른 사용자가 작성한 스토리 조회',
        operation_description='''
            다른 유저가 작성한 스토리를 조회합니다. 쿼리 파라미터 : email, search, filter <br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'preview': '서울숲. 가장 도시적인 단어...(최대 150자)',
                        'story_review': '"모두에게 열려있는 도심 속 가장 자연 친화적인 여가공간"',
                        'tag': '#생명 다양성 #자연 친화 #함께 즐기는',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'extra_pics': ['https://abc.com/2.jpg'],
                        'story_like': True,
                        'writer': 'sdptech@gmail.com',
                        'nickname': 'sdp_official',
                        'category': '식당 및 카페',
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        }
    )
    def get(self, request):

        filters_serializer = self.OtherCreatedStoryFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data
        target = request.query_params.get('email')

        try:
            user = User.objects.get(email=target)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        selector = UserCreatedStorySelector(user=user)

        other_user_stories = selector.list(
            search=filters.get('search', ''),
            filter=filters.get('filter', []),
        )

        serialized_stories = []
        for story in other_user_stories:
            story_data = {
                'id': story.id,
                'place_name' : story.place.place_name,
                'title': story.title,
                'preview': story.preview,
                'story_review': story.story_review,
                'tag': story.tag,
                'rep_pic': request.build_absolute_uri(story.rep_pic.url) if story.rep_pic else None,
                'extra_pics': [request.build_absolute_uri(pic) for pic in story.extra_pics] if story.extra_pics else [],
                'writer': UserSerializer(user).data['email'], 
                'nickname' : UserSerializer(user).data['nickname'],
                'category': story.category,
            }

            likes = StoryLikeSelector.likes(story.id, user=request.user)
            story_data['story_like'] = likes

            serialized_stories.append(story_data)

        return Response(serialized_stories, status=status.HTTP_200_OK)
    
    
class UserStoryLikeApi(APIView):
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(
        operation_id='마이페이지 스토리 좋아요 취소',
        operation_description='''
            전달된 id를 가지는 저장된 스토리글에 대한 사용자의 좋아요 취소 또는 좋아요를 수행합니다.<br/>
            결과로 좋아요 상태(TRUE:좋아요, FALSE:좋아요X)가 반환됩니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"story_like": True}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
        service = StoryCoordinatorService(
            user=request.user
        )
        story_like = service.like_or_dislike(
            story_id=request.data['id'],
        )
        return Response({
            'status': 'success',
            'data': {'story_like': story_like},
        }, status=status.HTTP_201_CREATED)
