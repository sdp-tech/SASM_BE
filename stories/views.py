from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
from stories.selectors import StoryLikeSelector
from stories.services import StoryCoordinatorService
from core.views import get_paginated_response

from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class StoryLikeApi(APIView, ApiAuthMixin):
    @swagger_auto_schema(
        operation_id='스토리 좋아요 또는 좋아요 취소',
        operation_description='''
            전달된 id를 가지는 스토리글에 대한 사용자의 좋아요/좋아요 취소를 수행합니다.<br/>
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
            "401": openapi.Response(
                description="Bad Request",    
            ),
        },
    )
    def post(self, request):
        try:
            service = StoryCoordinatorService(
                user = request.user
            )
            story_like = service.like_or_dislike(
                story_id=request.data['id'],
            )

            return Response({
                'status': 'success',
                'data': {'story_like': story_like},
            }, status=status.HTTP_201_CREATED)
        except:
            return Response({
                'status': 'fail',
                'message': '권한이 없거나 story가 존재하지 않습니다.',
            }, status=status.HTTP_401_UNAUTHORIZED)