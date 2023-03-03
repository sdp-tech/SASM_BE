from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
from stories.selectors import StoryCommentSelector
# from stories.services import StoryCoordinatorService, StoryCommentCoordinatorService
from core.views import get_paginated_response

from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class StoryCommentListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 20
        page_size_query_param = 'page_size'

    class StoryCommentListFilterSerializer(serializers.Serializer):
        story = serializers.IntegerField(required=True)
    
    class StoryCommentListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        story = serializers.IntegerField()
        content = serializers.CharField()
        isParent = serializers.BooleanField()
        group = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        mention = serializers.CharField()
        profile_image = serializers.ImageField()
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField()

    @swagger_auto_schema(
        operation_id='스토리 댓글 조회',
        operation_description='''
            해당 story의 하위 댓글을 조회합니다.<br/>
        ''',
        query_serializer=StoryCommentListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'content': '멋져요',
                        'isParent': True,
                        'group': 1,
                        'nickname': 'sdpygl',
                        'email': 'sdpygl@gmail.com',
                        'mention': 'sasm@gmail.com',
                        'profile_image': 'https://abc.com/1.jpg',
                        'created_at': '2019-08-24T14:15:22Z',
                        'updated_at': '2019-08-24T14:15:22Z',
                    }
                },
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        try:
            filters_serializer = self.StoryCommentListFilterSerializer(
                data=request.query_params)
            filters_serializer.is_valid(raise_exception=True)
            filters = filters_serializer.validated_data

            selector = StoryCommentSelector()

            story_comments = selector.list(
                story_id=filters.get('story')  #story id값 받아서 넣기
            )

        except:
            return Response({
                'status': 'fail',
                'message' : 'unknown',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return get_paginated_response(
                pagination_class=self.Pagination,
                serializer_class=self.StoryCommentListOutputSerializer,
                queryset=story_comments,
                request=request,
                view=self,
            )