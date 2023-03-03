from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
from stories.selectors import StoryCoordinatorSelector, StorySelector, semi_category, StoryLikeSelector
# from stories.services import StoryCoordinatorService, StoryCommentCoordinatorService
from core.views import get_paginated_response

from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class StoryDetailApi(APIView):
    class StoryDetailOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        story_review = serializers.CharField()
        tag = serializers.CharField()
        html_content = serializers.CharField()
        story_like = serializers.BooleanField()
        views = serializers.IntegerField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        semi_category = serializers.CharField()

    @swagger_auto_schema(
        operation_id='스토리 글 조회',
        operation_description='''
            전달된 id에 해당하는 스토리 디테일을 조회합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'category': '녹색 공간',
                        'semi_category': '반려동물 출입 가능, 텀블러 사용 가능, 비건',
                        'tag': '#생명 다양성 #자연 친화 #함께 즐기는',
                        'story_review': '"모두에게 열려있는 도심 속 가장 자연 친화적인 여가공간"',
                        'html_content': '서울숲. 가장 도시적인 단어...(최대 150자)',
                        'views': 45,
                        'story_like': True,
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        try:
            selector = StoryCoordinatorSelector(
                user=request.user
            )
            story = selector.detail(
                story_id=request.data['id'])
            print('detail: ', story)
            serializer = self.StoryDetailOutputSerializer(story)

            return Response({
                'status': 'success',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)
        except:
            return Response({
                'status': 'fail',
                'message': '해당 스토리가 존재하지 않습니다.',
            })