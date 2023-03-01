from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
from stories.selectors import StorySelector, semi_category
# from stories.services import StoryCoordinatorService, StoryCommentCoordinatorService
from core.views import get_paginated_response
from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class StoryListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class StoryListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        latest = serializers.BooleanField(required=False)

    class StoryListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        preview = serializers.CharField()
        rep_pic = serializers.ImageField()
        views = serializers.IntegerField()
        story_like = serializers.BooleanField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        semi_category = serializers.SerializerMethodField()

        def get_semi_category(self, obj):
            result = semi_category(obj.id)
            return result
        
    @swagger_auto_schema(
        operation_id='스토리 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 게시글 리스트를 반환합니다.<br/>
            <br/>
            search : 제목 혹은 장소 검색어<br/>
            latest : 최신순 정렬 여부 (ex: true)</br>
            ''',
        query_serializer=StoryListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'category': '녹색 공간',
                        'semi_category': '반려동물 출입 가능, 오보',
                        'preview': '서울숲. 가장 도시적인 단어...(최대 150자)',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'story_like': True,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.StoryListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data
        story = StorySelector.list(
            search=filters.get('search', ''),
            latest=filters.get('latest', True),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.StoryListOutputSerializer,
            queryset=story,
            request=request,
            view=self
        )