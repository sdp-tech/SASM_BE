from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
from stories.selectors import StorySelector
# from stories.services import StoryCoordinatorService, StoryCommentCoordinatorService
from core.views import get_paginated_response
from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class StoryRecommendApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class StoryRecommendListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        created = serializers.DateTimeField()
        
    @swagger_auto_schema(
        operation_id='story의 category와 같은 스토리 추천 리스트',
        operation_description='''
            해당 스토리의 category와 같은 스토리 리스트를 반환합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        try:
            recommend_story = StorySelector.recommend_list(
                story_id = request.data['id']
            )
        except:
            return Response({
                'status': 'fail',
                'message': 'unknown',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return get_paginated_response(
                pagination_class=self.Pagination,
                serializer_class=self.StoryRecommendListOutputSerializer,
                queryset=recommend_story,
                request=request,
                view=self
            )
