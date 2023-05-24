
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from users.mixins import ApiAuthMixin,  ApiAllowAnyMixin
from mypage.services import  UserFollowService
from mypage.selectors.follow_selectors import  UserFollowSelector
from users.models import User

from core.views import get_paginated_response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema



class UserDoUndoFollowApi(ApiAuthMixin, APIView):
    class UserFollowInputSerializer(serializers.Serializer):
        targetEmail = serializers.CharField()

        class Meta:
            examples = {
                'targetEmail': 'sdgygl@gmail.com'
            }

    @swagger_auto_schema(
        operation_id='타유저 팔로우/언팔로우',
        operation_description='''
            전달된 targetEmail에 해당하는 유저에 대해 팔로우/언팔로우를 수행합니다.<br/>
            결과로 팔로우 상태(true: 팔로잉 중, false: 팔로잉 x)가 반환됩니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"follows": True}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
        serializer = self.UserFollowInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        target_user = get_object_or_404(
            User, email=data.get('targetEmail'))
        follows = UserFollowService.follow_or_unfollow(
            source=request.user,
            target=target_user)

        return Response({
            'status': 'success',
            'data': {'follows': follows},
        }, status=status.HTTP_200_OK)


class UserFollowingListApi(ApiAllowAnyMixin, APIView):
    class Pagination(PageNumberPagination):
        page_size = 5
        page_size_query_param = 'page_size'

    class UserFollowingListFilterSerializer(serializers.Serializer):
        email = serializers.CharField(required=True)
        page = serializers.IntegerField(required=False)
        #소스 이메일 변수 추가
        source_email = serializers.CharField(required=True, allow_blank=True) 
        
    class UserFollowingListOutputSerializer(serializers.Serializer):
        email = serializers.CharField()
        nickname = serializers.CharField()
        profile_image = serializers.ImageField()
    
    @swagger_auto_schema(
        operation_id='유저 팔로잉 리스트',
        operation_description='''
            유저가 팔로우한 유저의 리스트를 반환합니다.<br/>
        ''',
        query_serializer=UserFollowingListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'email': 'sdpygl@gmail.com',
                        'nickname': 'sdpygl',
                        'profile_image': 'https://abc.com/1.jpg',
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.UserFollowingListFilterSerializer(
            data=request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        target_user = get_object_or_404(User, email=filters.get('email'))
        followings = UserFollowSelector.get_following_with_filter(
            source_email=filters.get('source_email'),
            target_email=target_user.email
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserFollowingListOutputSerializer,
            queryset=followings,
            request=request,
            view=self
        )

class UserFollowerListApi(ApiAllowAnyMixin, APIView):
    class Pagination(PageNumberPagination):
        page_size = 5
        page_size_query_param = 'page_size'

    class UserFollowerListFilterSerializer(serializers.Serializer):
        email = serializers.CharField(required=True)
        page = serializers.IntegerField(required=False)
        source_email = serializers.CharField(required =True,allow_blank=True)

    class UserFollowerListOutputSerializer(serializers.Serializer):
        email = serializers.CharField()
        nickname = serializers.CharField()
        profile_image = serializers.ImageField()

    @swagger_auto_schema(
        operation_id='유저 팔로워 리스트',
        operation_description='''
            유저를 팔로우한 유저의 리스트를 반환합니다.<br/>
        ''',
        query_serializer=UserFollowerListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'email': 'sdpygl@gmail.com',
                        'nickname': 'sdpygl',
                        'profile_image': 'https://abc.com/1.jpg',
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.UserFollowerListFilterSerializer(
            data=request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        target_user = get_object_or_404(User, email=filters.get('email'))
        followers = UserFollowSelector.get_follower_with_filter(
            source_email=filters.get('source_email'),
            target_email=target_user.email
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserFollowerListOutputSerializer,
            queryset=followers,
            request=request,
            view=self
        )
