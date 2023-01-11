import io
import datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.core.files.images import ImageFile
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import ValidationError

from .models import Board, Post, PostComment, PostCommentPhoto, PostReport, PostCommentReport
from users.models import User
from .serializers import PostCommentSerializer, PostCommentCreateSerializer, PostCommentUpdateSerializer, PostReportSerializer, PostCommentReportSerializer
from core.permissions import CommentWriterOrReadOnly
from sasmproject.swagger import PostCommentViewSet_list_params, param_id
from drf_yasg.utils import swagger_auto_schema
from itertools import chain

class PostCommentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


class PostCommentView(viewsets.ModelViewSet):
    '''
        Post 하위 comment 관련 작업 API
    '''
    queryset = PostComment.objects.all().order_by('id')
    serializer_class = PostCommentSerializer
    permission_classes = [
        CommentWriterOrReadOnly
    ]
    pagination_class = PostCommentPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCommentCreateSerializer
        elif self.action == 'update':
            return PostCommentUpdateSerializer
        return PostCommentSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
 
    @swagger_auto_schema(operation_id='api_post_comments_get')
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'status': 'success',
            'data': response.data,
        }, status=status.HTTP_200_OK)   

    @swagger_auto_schema(operation_id='api_post_comments_list')
    def list(self, request, *args, **kwargs):
        '''특정 게시글 하위 댓글 조회'''

        post_id = request.GET.get('post')

        serializer = self.get_serializer(
            PostComment.objects.filter(post=post_id),
            many=True,
            context={
                "post": Post.objects.get(id=post_id),
            }
        )
        # 댓글, 대댓글별 pagination 따로 사용하는 대신, 댓글 group(parent+childs)별로 정렬
        # 댓글의 경우 id값을, 대댓글의 경우 parent(상위 댓글의 id)값을 대표값으로 설정해 정렬(tuple의 1번째 값)
        # 댓글 group 내에서는 id 값을 기준으로 정렬(tuple의 2번째 값)
        serializer_data = sorted(
            serializer.data, key=lambda k: (k['parent'], k['id']) if k['parent'] else (k['id'], k['id']))
        page = self.paginate_queryset(serializer_data)

        if page is not None:
            serializer = self.get_paginated_response(page)
        else:
            serializer = self.get_serializer(page, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_post_comments_post')
    def create(self, request, *args, **kwargs):
        try:
            super().create(request, *args, **kwargs)

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
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_post_comments_patch')
    def update(self, request, pk, *args, **kwargs):
        try:
            # partial update                   
            kwargs['partial'] = True
            super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response({
                'status': 'fail',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({
                'status': 'fail',
                'message': 'unknown',
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_post_comments_delete')
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class ReportPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


class ReportListView(viewsets.ModelViewSet):
    '''
        Report의 list 정보를 주는 API
    '''
    pagination_class = ReportPagination

    #retrieve에 사용
    serializer_class_post_report = PostReportSerializer
    serializer_class_post_comment_report = PostCommentReportSerializer

    @swagger_auto_schema(operation_id='api_report_get', manual_parameters=[PostCommentViewSet_list_params])
    def list(self, request):
        post_report_queryset = PostReport.objects.all()
        post_comment_report_queryset = PostCommentReport.objects.all()

        serializer_post_report = self.serializer_class_post_report(post_report_queryset, many=True).data
        serializer_post_comment_report = self.serializer_class_post_comment_report(post_comment_report_queryset, many=True).data
        serializer_data = serializer_post_report + serializer_post_comment_report

        page = self.paginate_queryset(serializer_data)

        if page is not None:
            serializer = self.get_paginated_response(page)
            return Response({
                'status': 'success',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'fail',
                'message': 'unknown',
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_id='api_report_post')
    @action(detail=False, methods=['post'])
    def create(self, request):
        #게시글 신고
        if 'post' in request.POST :
            post_report_info = request.data
            serializer = PostReportSerializer(data=post_report_info, context={'request': request})
            try:
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        "status" : "success",
                        "data" : serializer.data,
                    }, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({
                    'status': 'fail',
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                return Response({
                    'status': 'fail',
                    'message': 'unknown',
                }, status=status.HTTP_400_BAD_REQUEST)
        #댓글 신고
        elif 'comment' in request.POST :
            post_comment_report_info =request.data
            serializer = PostCommentReportSerializer(data=post_comment_report_info, context={'request': request})
            try:
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        "status" : "success",
                        "data" : serializer.data,
                    }, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({
                    'status': 'fail',
                    'message': str(e),
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                return Response({
                    'status': 'fail',
                    'message': 'unknown',
                }, status=status.HTTP_400_BAD_REQUEST)


class PostReportView(viewsets.ModelViewSet):
    '''
        Post Report 관련 작업 API
    '''    
    queryset = PostReport.objects.all()
    serializer_class = PostReportSerializer
    # permission_class = [
    #     AllowAny,
    # ]
    pagination_class = ReportPagination
  
    @swagger_auto_schema(operation_id='api_post_report_delete')
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class PostCommentReportView(viewsets.ModelViewSet):
    '''
        Post Comment Report 관련 작업 API
    '''    
    queryset = PostCommentReport.objects.all()
    serializer_class = PostCommentReportSerializer
    # permission_class = [
    #     AllowAny,
    # ]
    pagination_class = ReportPagination 

    @swagger_auto_schema(operation_id='api_post_comment_report_delete')
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)