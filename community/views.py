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

from .models import Board, Post, PostComment, PostReport, PostCommentReport
from users.models import User
from users.serializers import UserSerializer
from .serializers import PostDetailSerializer, PostCommentSerializer, PostCommentCreateSerializer, PostCommentUpdateSerializer, PostReportCreateSerializer, PostCommentReportCreateSerializer
from core.permissions import CommentWriterOrReadOnly
from sasmproject.swagger import PostCommentViewSet_list_params, param_id, PostLikeView_post_params
from drf_yasg.utils import swagger_auto_schema
from itertools import chain

class BoardPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'

class PostDetailView(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created')
    serializer_class = PostDetailSerializer
    pagination_class = BoardPagination
    
    def get_permissions(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'destroy':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(operation_id='api_community_post_post')
    @action(detail=False, methods=['post'])
    def create(self, request):
        serializer = PostDetailSerializer(data=request.data, context={'request': request})
        print(serializer)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                    "status" : "success",
                    "data" : serializer.data,
                },status=status.HTTP_200_OK)
        return Response({
                "status" : "fail",
                "data" : serializer.errors,
            })

    @swagger_auto_schema(operation_id='api_community_post_put')
    def update(self, request, *args, **kwargs):
        print('aaaaa')
        try:
            kwargs['partial'] = True
            super().update(request, *args, **kwargs)  #Serializer에서 update와 create 기능이 동일해서 create부름
        except ValidationError as e:
            return Response({
                'status': 'fail',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'message': 'updated',
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(operation_id='api_community_post_get')
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'status': 'success',
            'data': response.data,
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_community_post_delete')
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)

class PostLikeView(viewsets.ModelViewSet):
    serializer_class = PostDetailSerializer
    queryset = Post.objects.all()
    permission_classes = [
        IsAuthenticated,
    ]

    @swagger_auto_schema(operation_id='api_community_post_like_user_get')
    def get(self, request, pk):
        '''
            게시글을 좋아요한 유저 list를 반환하는 API
        '''
        post = get_object_or_404(Post, pk=pk)
        like_id = post.post_likeuser_set.all()
        users = User.objects.filter(id__in=like_id)
        serializer = UserSerializer(users, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_community_like_post',
                        request_body=PostLikeView_post_params,
                        responses={200:'success'})
    def post(self, request):
        '''
            좋아요 및 좋아요 취소를 수행하는 API
        '''
        id = request.data['id']
        print(id)
        post = get_object_or_404(Post, pk=id)
        if request.user.is_authenticated:
            user = request.user
            profile = User.objects.get(email=user)
            check_like = post.post_likeuser_set.filter(pk=profile.pk)

            if check_like.exists():
                post.post_likeuser_set.remove(profile)
                post.like_cnt -= 1
                post.save()
                return Response({
                    'status': 'success',
                    'message': 'removed',
                }, status=status.HTTP_200_OK)
            else:
                post.post_likeuser_set.add(profile)
                post.like_cnt += 1
                post.save()
                return Response({
                    'status': 'success',
                    'message': 'added',
                }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'fail',
                'data': { "user" : "user is not authenticated"},
            }, status=status.HTTP_401_UNAUTHORIZED)


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


class PostReportView(viewsets.ModelViewSet):
    '''
        Post Report 관련 작업 API
    '''    
    queryset = PostReport.objects.all()
    serializer_class = PostReportCreateSerializer #Read, Update, Delete at sdp_admin app
    permission_class = [IsAuthenticated,]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @swagger_auto_schema(operation_id='api_post_report_create')
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


class PostCommentReportView(viewsets.ModelViewSet):
    '''
        Post Comment Report 관련 작업 API
    '''    
    queryset = PostCommentReport.objects.all()
    serializer_class = PostCommentReportCreateSerializer #Read, Update, Delete at sdp_admin app
    permission_class = [IsAuthenticated,]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @swagger_auto_schema(operation_id='api_post_comment_report_create')
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