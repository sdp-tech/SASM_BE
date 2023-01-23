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
from rest_framework import serializers

from rest_framework.views import APIView
from community.mixins import ApiAuthMixin
from community.services import PostCoordinatorService
from community.selectors import PostCoordinatorSelector, PostHashtagSelector

from .models import Post, PostComment, PostReport, PostCommentReport, PostHashtag
from users.models import User
from .serializers import PostCommentSerializer, PostCommentCreateSerializer, PostCommentUpdateSerializer, PostReportCreateSerializer, PostCommentReportCreateSerializer
from core.permissions import CommentWriterOrReadOnly
from sasmproject.swagger import PostCommentViewSet_list_params, param_id
from drf_yasg.utils import swagger_auto_schema


class PostCreateApi(APIView, ApiAuthMixin):
    class InputSerializer(serializers.Serializer):
        board = serializers.IntegerField()
        title = serializers.CharField()
        content = serializers.CharField()
        hashtagList = serializers.ListField(required=False)
        imageList = serializers.ListField(required=False)

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PostCoordinatorService(
            user=request.user
        )

        # request body가 json 방식이 아닌 multipart/form-data 방식으로 전달
        post = service.create(
            board_id=request.POST.get('board'),
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            hashtag_names=request.POST.getlist(
                'hashtagList') if 'hashtagList' in request.POST else None,
            image_files=request.FILES.getlist(
                'imageList') if 'imageList' in request.FILES else None,
        )

        return Response({
            'status': 'success',
            'data': {'id': post.id},
        }, status=status.HTTP_201_CREATED)


class PostUpdateApi(APIView, ApiAuthMixin):
    class InputSerializer(serializers.Serializer):
        title = serializers.CharField()
        content = serializers.CharField()
        hashtagList = serializers.ListField(required=False)
        photoList = serializers.ListField(required=False)
        imageList = serializers.ListField(required=False)

    def patch(self, request, post_id):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PostCoordinatorService(
            user=request.user
        )

        post = service.update(
            post_id=post_id,
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            hashtag_names=request.POST.getlist(
                'hashtagList') if 'hashtagList' in request.POST else [],
            photo_image_urls=request.POST.getlist(
                'photoList') if 'photoList' in request.POST else [],
            image_files=request.FILES.getlist(
                'imageList') if 'imageList' in request.FILES else [],
        )

        return Response({
            'status': 'success',
            'data': {'id': post.id},
        }, status=status.HTTP_200_OK)


class PostDeleteApi(APIView, ApiAuthMixin):
    def delete(self, request, post_id):

        service = PostCoordinatorService(
            user=request.user
        )

        service.delete(
            post_id=post_id
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class PostLikeApi(APIView, ApiAuthMixin):
    def post(self, request, post_id):
        service = PostCoordinatorService(
            user=request.user
        )

        likes = service.like_or_dislike(
            post_id=post_id
        )

        return Response({
            'status': 'success',
            'data': {'likes': likes},
        }, status=status.HTTP_200_OK)


def get_paginated_response(*, pagination_class, serializer_class, queryset, request, view):
    paginator = pagination_class()

    page = paginator.paginate_queryset(queryset, request, view=view)

    if page is not None:
        serializer = serializer_class(page, many=True)
    else:
        serializer = serializer_class(queryset, many=True)

    return Response({
        'status': 'success',
        'data': serializer.data,
    }, status=status.HTTP_200_OK)


class PostListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    class FilterSerializer(serializers.Serializer):
        board = serializers.CharField(required=True)
        query = serializers.CharField(required=False)
        query_type = serializers.CharField(required=False)
        latest = serializers.BooleanField(required=False)

    class OutputSerializer(serializers.Serializer):
        title = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        like_cnt = serializers.IntegerField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()

        # 게시판 지원 기능에 따라 전달 여부 결정되는 필드
        commentCount = serializers.IntegerField(required=False)

    def get(self, request):
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = PostCoordinatorSelector(
            user=request.user
        )
        posts = selector.list(
            board_id=filters['board'],  # 게시판 id
            # 검색어
            query=filters['query'] if 'query' in filters else '',
            # 검색어 종류 (해시태그 검색 여부)
            query_type=filters['query_type'] if 'query_type' in filters else '',
            # 최신순 정렬 여부 (기본값: 최신순)
            latest=filters['latest'] if 'latest' in filters else True,
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=posts,
            request=request,
            view=self
        )


# class CommaSeperatedStringToListField(serializers.CharField):
#     def to_representation(self, obj):
#         if not obj:  # 빈(empty) 문자열일 경우
#             return []
#         return obj.split(',')

#     def to_internal_value(self, data):
#         return super().to_internal_value(self, ",".join(data))


class PostDetailApi(APIView):
    class OutputSerializer(serializers.Serializer):
        title = serializers.CharField()
        content = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()

        like_cnt = serializers.IntegerField()
        view_cnt = serializers.IntegerField()
        likes = serializers.BooleanField()

        # 게시판 지원 기능에 따라 전달 여부 결정되는 필드
        hashtagList = serializers.ListField(required=False)
        photoList = serializers.ListField(required=False)

    def get(self, request, post_id):
        selector = PostCoordinatorSelector(
            user=request.user
        )
        post = selector.detail(
            post_id=post_id)

        serializer = self.OutputSerializer(post)

        return Response(serializer.data)


class PostHashtagListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    class FilterSerializer(serializers.Serializer):
        query = serializers.CharField(required=True)

    class OutputSerializer(serializers.Serializer):
        name = serializers.CharField()
        postCount = serializers.IntegerField()

    def get(self, request):
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = PostHashtagSelector()
        hashtags = selector.list(
            query=filters['query']  # 해당 검색어로 시작하는 모든 해시태그 리스트
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=hashtags,
            request=request,
            view=self
        )


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

    @ swagger_auto_schema(operation_id='api_post_comments_get')
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'status': 'success',
            'data': response.data,
        }, status=status.HTTP_200_OK)

    @ swagger_auto_schema(operation_id='api_post_comments_list')
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

    @ swagger_auto_schema(operation_id='api_post_comments_post')
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

    @ swagger_auto_schema(operation_id='api_post_comments_patch')
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

    @ swagger_auto_schema(operation_id='api_post_comments_delete')
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
    # Read, Update, Delete at sdp_admin app
    serializer_class = PostReportCreateSerializer
    permission_class = [IsAuthenticated, ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @ swagger_auto_schema(operation_id='api_post_report_create')
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
    # Read, Update, Delete at sdp_admin app
    serializer_class = PostCommentReportCreateSerializer
    permission_class = [IsAuthenticated, ]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @ swagger_auto_schema(operation_id='api_post_comment_report_create')
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
