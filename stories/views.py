from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
# from stories.selectors import StoryCoordinatorSelector, StorySelector, StoryCommentSelector, MapMarkerSelector, semi_category, StoryLikeSelector
from stories.services import StoryCommentCoordinatorService
from core.views import get_paginated_response

from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class StoryCommentCreateApi(APIView, ApiAuthMixin):
    class StoryCommentCreateInputSerializer(serializers.Serializer):
        story=serializers.IntegerField()
        content = serializers.CharField()
        isParent = serializers.BooleanField()
        parent = serializers.IntegerField(required=False)
        mention = serializers.CharField(required=False)
        
        class Meta:
            examples = {
                'id': 1,
                'story': 1,
                'content': '정보 부탁드려요.',
                'isParent': True,
                'parent': 1,
                'mentionEmail': 'sdpygl@gmail.com',
            }

        def validate(self, data):
            print('data:' , data)
            # print('par', data['parent'])
            if 'parent' in data:
                parent = StoryComment.objects.get(id=data['parent'])
                # child comment를 parent로 설정 시 reject
                if parent and not parent.isParent:
                    raise ValidationError(
                        'can not set the child comment as parent comment')
                # parent가 null이 아닌데(자신이 child), isParent가 true인 경우 reject
                if parent is not None and data['isParent']:
                    raise ValidationError(
                        'child comment has isParent value be false')
            # parent가 null인데(자신이 parent), isParent가 false인 경우 reject
            elif 'parent' not in data and not data['isParent']:
                raise ValidationError(
                    'parent comment has isParent value be true')
            return data   
        
    @swagger_auto_schema(
        request_body=StoryCommentCreateInputSerializer,
        security=[],
        operation_id='스토리 댓글 생성',
        operation_description='''
            전달된 필드를 기반으로 해당 스토리의 댓글을 생성합니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"id": 1}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),        
        },    
    )

    def post(self, request):
        try:
            serializer = self.StoryCommentCreateInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            service = StoryCommentCoordinatorService(
                user=request.user
            )
            story_comment = service.create(
                story_id=data.get('story'),
                content=data.get('content'),
                isParent=data.get('isParent'),
                parent_id=data.get('parent', None),
                mentioned_email=data.get('mention', '')
            )
        
        except ValidationError as e:
            return Response({
                'status': 'fail',
                'message': str(e),
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