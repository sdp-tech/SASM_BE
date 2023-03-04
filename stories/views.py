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


class StoryCommentUpdateApi(APIView, ApiAuthMixin):
    class StoryCommnetUpdateInputSerializer(serializers.Serializer):
        content = serializers.CharField()
        mentionEmail = serializers.CharField(required=False)

        class Meta:
            examples = {
                'content': '저도요!!',
                'mentionEmail': 'sdppp@gamil.com',
            }

    @swagger_auto_schema(
        request_body=StoryCommnetUpdateInputSerializer,
        security=[],
        operation_id='스토리 댓글 수정',
        operation_description='''
            전달된 id에 해당하는 댓글을 업데이트합니다.<br/>
            전송된 모든 필드 값을 그대로 댓글에 업데이트하므로, 댓글에 포함되어야 하는 모든 필드 값이 request body에 포함되어야합니다.<br/>
            즉, 값이 수정된 필드뿐만 아니라 값이 그대로 유지되어야하는 필드도 함께 전송되어야합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"id": 1}
                    }
                },
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def patch(self, request, story_comment_id):
        try:
            story_comment = StoryComment.objects.get(id=story_comment_id)
            serializers = self.StoryCommnetUpdateInputSerializer(data=request.data)
            serializers.is_valid(raise_exception=True)
            data = serializers.validated_data

            service = StoryCommentCoordinatorService(
                user=request.user
            )

            story_comment = service.update(
                story_comment_id=story_comment_id,
                content=data.get('content'),
                mentioned_email=data.get('mentionEmail', ''),
            )
        except ValidationError as e:
            return Response({
                'status': 'fail',
                'data': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'fail',
                'message': 'unknown',
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'data': {'id': story_comment.id},
        }, status=status.HTTP_200_OK)
