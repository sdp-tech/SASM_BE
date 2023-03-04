from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
from stories.selectors import StoryCommentSelector
from stories.services import StoryCommentCoordinatorService
from core.views import get_paginated_response

from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema



class StoryCommentDeleteApi(APIView, ApiAuthMixin):
    @swagger_auto_schema(
        operation_id='스토리 댓글 삭제',
        operation_description='''
            전달받은 id에 해당하는 댓글을 삭제합니다<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",     
            ),
            "400": openapi.Response(
                description="Bad Request",
            )        
        },
    )
    def delete(self, request, story_comment_id):
        try:
            service = StoryCommentCoordinatorService(
                user=request.user
            )
            service.delete(
                story_comment_id=story_comment_id
            )
        except:
            return Response({
                'statusf': 'fail',
                'message': 'unknown',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)