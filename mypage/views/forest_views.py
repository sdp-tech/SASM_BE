import re
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from users.mixins import ApiAuthMixin,  ApiAllowAnyMixin
from mypage.selectors.curations_selectors import CurationSelector
from mypage.selectors.forest_selectors import UserForestSelector, UserCreatedForestSelector
from users.models import User
from forest.models import Forest
from forest.permissions import IsWriter
from forest.selectors import ForestSelector
from forest.services import ForestService

from core.views import get_paginated_response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class UserForestListApi(APIView):
    permission_classes = (IsAuthenticated, )

    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class UserForestFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        category_filter = serializers.ListField(required=False)

    class UserForestOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        preview = serializers.SerializerMethodField()
        forest_like = serializers.SerializerMethodField()
        rep_pic = serializers.ImageField()
        writer = serializers.CharField()
        nickname = serializers.CharField()
        writer_is_verified = serializers.BooleanField()

        def get_preview(self, obj):
            forest = get_object_or_404(Forest, id=obj.id)
            ret = re.sub(r'<img.*?>', ' ', forest.content)
            ret = re.sub(r'<.*?>', '', ret)  # FYI: 닫는 태그 <\/.+?>
            ret = re.sub(r'\s{2,}', ' ', ret)  # space 두개 이상인 경우 하나로
            return ret[:100]

        def get_forest_like(self, obj):
            re_user = self.context['request'].user
            likes = ForestSelector.likes(obj, user=re_user)
            return likes

    @swagger_auto_schema(
        query_serializer=UserForestFilterSerializer,
        operation_id='마이페이지 내가 좋아요한 포레스트 리스트',
        operation_description='''
            내가 좋아요한 포레스트 게시글을 불러옵니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': "신재생 에너지 종류",
                        'preview': '풍력발전이란? 풍력발전은 바람과 ...',
                        'forest_likes': True,
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer': 'sdpofficial',
                        'nickname': 'sdpygl',
                        'writer_is_verified': True,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.UserForestFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = UserForestSelector(user=request.user)
        like_forest = selector.list(
            search=filters.get('search', ''),
            category_filter=filters.get('category_filter', []),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserForestOutputSerializer,
            queryset=like_forest,
            request=request,
            view=self,
        )
    

class UserCreateForestApi(APIView):
    permission_classes = (IsWriter, )

    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class UserCreatedForestFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        category_filter = serializers.ListField(required=False)

    class UserCreatedForestOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        preview = serializers.SerializerMethodField()
        forest_like = serializers.SerializerMethodField()
        rep_pic = serializers.ImageField()
        writer = serializers.CharField()
        nickname = serializers.CharField()
        writer_is_verified = serializers.BooleanField()

        def get_preview(self, obj):
            forest = get_object_or_404(Forest, id=obj.id)
            ret = re.sub(r'<img.*?>', ' ', forest.content)
            ret = re.sub(r'<.*?>', '', ret)  # FYI: 닫는 태그 <\/.+?>
            ret = re.sub(r'\s{2,}', ' ', ret)  # space 두개 이상인 경우 하나로
            return ret[:100]

        def get_forest_like(self, obj):
            re_user = self.context['request'].user
            likes = ForestSelector.likes(obj, user=re_user)
            return likes

    @swagger_auto_schema(
        query_serializer=UserCreatedForestFilterSerializer,
        operation_id='마이페이지 내가 작성한 포레스트 리스트',
        operation_description='''
            내가 작성한 포레스트 게시글을 불러옵니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': "신재생 에너지 종류",
                        'preview': '풍력발전이란? 풍력발전은 바람과 ...',
                        'forest_likes': True,
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer': 'sdpofficial',
                        'nickname': 'sdpygl',
                        'writer_is_verified': True,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.UserCreatedForestFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data
        
        selector = UserCreatedForestSelector(user=request.user)
        user_forest = selector.list(
            search=filters.get('search', ''),
            category_filter=filters.get('category_filter', []),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserCreatedForestOutputSerializer,
            queryset=user_forest,
            request=request,
            view=self,
        )
    

class UserForestLikeApi(APIView):
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(
        operation_id='마이페이지 포레스트 좋아요 및 좋아요 취소',
        operation_description='''
            전달된 id를 가지는 저장된 포레스트 게시글에 대한 사용자의 좋아요 취소 또는 좋아요를 진행합니다.<br/>
            결과로 좋아요 상태(TRUE:좋아요, FALSE:좋아요X)가 반환됩니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"forest_like": True}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
        forest_id=request.data['id']

        forest_like = ForestService.like_or_dislike(
            forest=get_object_or_404(Forest, pk=forest_id),
            user=request.user
        )

        return Response({
            'status': 'success',
            'data': {'forest_like': forest_like},
        }, status=status.HTTP_200_OK)
