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
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class PostCreateApi(APIView, ApiAuthMixin):
    class PostCreateInputSerializer(serializers.Serializer):
        board = serializers.IntegerField()
        title = serializers.CharField()
        content = serializers.CharField()
        hashtagList = serializers.ListField(required=False)
        imageList = serializers.ListField(required=False)

        class Meta:
            examples = {
                'board': 1,
                'title': '안녕 상점 추천합니다.',
                'content': '개인적으로 좋았습니다.',
                'hashtagList': ['안녕', '상점'],
                'imageList': ['<IMAGE FILE BINARY>', '<IMAGE FILE BINARY>'],
            }

    @swagger_auto_schema(
        request_body=PostCreateInputSerializer,
        # query_serializer=CategorySerializer,
        security=[],
        operation_id='커뮤니티 게시글 생성',
        operation_description='''
            전달된 필드를 기반으로 게시글을 생성합니다.<br/>
            board 필드는 게시글을 생성할 게시판의 식별자로, <br/>
                1: 자유게시판<br/>
                2: 장소추천게시판<br/>
                3. 홍보게시판<br/>
                4. 모임게시판<br/>
            으로 설정되어 있습니다.<br/>
            <br/>
            hashtagList, imageList는 해당 게시판의 속성(게시글 해시태그 지원여부, 게시글 이미지 지원 여부 등)에 따라 선택적으로 포함될 수 있습니다.<br/>
            참고로 request body는 json 형식이 아닌 <b>multipart/form-data 형식</b>으로 전달받으므로, 리스트 값을 전달하고자 한다면 개별 원소들마다 리스트 필드 이름을 key로 설정하여, 원소 값을 value로 추가해주면 됩니다.<br/>
            가령 hashtagList의 경우, (key: 'hashtagList', value: '안녕'), (key: 'hashtagList', value: '상점') 과 같이 request body에 포함해주면 됩니다.<br/>
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
        serializer = self.PostCreateInputSerializer(data=request.data)
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
    class PostUpdateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        content = serializers.CharField()
        hashtagList = serializers.ListField(required=False)
        photoList = serializers.ListField(required=False)
        imageList = serializers.ListField(required=False)

        class Meta:
            examples = {
                'title': '안녕 상점 추천합니다.',
                'content': '개인적으로 좋았습니다.',
                'hashtagList': ['안녕', '지속가능성'],
                'photoList': ['https://abc.com/2.jpg'],
                'imageList': ['<IMAGE FILE BINARY>', '<IMAGE FILE BINARY>'],
            }

    @swagger_auto_schema(
        request_body=PostUpdateInputSerializer,
        # query_serializer=CategorySerializer,
        security=[],
        operation_id='커뮤니티 게시글 업데이트',
        operation_description='''
            전송된 모든 필드 값을 그대로 게시글에 업데이트하므로, 게시글에 포함되어야 하는 모든 필드 값이 request body에 포함되어야합니다.<br/>
            즉, 값이 수정된 필드뿐만 아니라 값이 그대로 유지되어야하는 필드도 함께 전송되어야합니다.<br/>
            <br/>
            hashtagList, photoList, imageList는 해당 게시판의 속성(게시글 해시태그 지원여부, 게시글 이미지 지원 여부 등)에 따라 선택적으로 포함될 수 있습니다.<br/>
            hashtagList 사용 예시로, 게시글 디테일 API에서 전달받은 hashtagList 값이 ['안녕', '상점']일때, '상점' 해시태그를 지우고, '지속가능성' 해시태그를 새로 추가하고 싶다면 ['안녕', '지속가능성']으로 값을 설정하면 됩니다.<br/>
            photoList 사용 예시로, 게시글 디테일 API에서 전달받은 photoList 값이 ['https://abc.com/1.jpg', 'https://abc.com/2.jpg']일 때 '1.jpg'를 지우고 싶다면 ['https://abc.com/2.jpg']으로 값을 설정하면 됩니다.<br/>
            만약 새로운 photo를 추가하고 싶다면, imageList에 이미지 첨부 파일을 1개 이상 담아 전송하면 됩니다.<br/>
            <br/>
            참고로 request body는 json 형식이 아닌 <b>multipart/form-data 형식</b>으로 전달받으므로, 리스트 값을 전달하고자 한다면 개별 원소들마다 리스트 필드 이름을 key로 설정하여, 원소 값을 value로 추가해주면 됩니다.<br/>
            가령 hashtagList의 경우, (key: 'hashtagList', value: '안녕'), (key: 'hashtagList', value: '상점') 과 같이 request body에 포함해주면 됩니다.<br/>
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
    def put(self, request, post_id):
        serializer = self.PostUpdateInputSerializer(data=request.data)
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

    @swagger_auto_schema(
        operation_id='커뮤니티 게시글 삭제',
        operation_description='''
            전달된 id를 가지는 게시글을 삭제합니다.<br/>
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

    @swagger_auto_schema(
        operation_id='커뮤니티 게시글 좋아요/좋아요 취소',
        operation_description='''
            전달된 id를 가지는 게시글에 대한 사용자의 좋아요/좋아요 취소를 수행합니다.<br/>
            결과로 좋아요 상태(true: 좋아요, false: 좋아요 x)가 반환됩니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"likes": True}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
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

    class PostListFilterSerializer(serializers.Serializer):
        board = serializers.CharField(required=True)
        query = serializers.CharField(required=False)
        query_type = serializers.CharField(required=False)
        latest = serializers.BooleanField(required=False)

    class PostListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        likeCount = serializers.IntegerField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()

        # 게시판 지원 기능에 따라 전달 여부 결정되는 필드
        commentCount = serializers.IntegerField(required=False)

    @swagger_auto_schema(
        operation_id='커뮤니티 게시글 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 게시글 리스트를 반환합니다.<br/>
            <br/>
            query: 검색어 (ex: '지속가능성')</br>
            query_type: 검색 종류 (ex: 'default', 'hashtag')</br>
            latest: 최신순 정렬 여부 (ex: true)</br>
            <br/>
            기본 검색의 경우, 전달된 query를 title이나 content에 포함하고 있는 게시글 리스트를 반환합니다.<br/>
            해시태그 검색의 경우, 전달된 query와 정확히 일치하는 해시태그를 갖는 게시글 리스트를 반환합니다.<br/>
        ''',
        query_serializer=PostListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '안녕 상점 추천합니다.',
                        'nickname': 'sdpygl',
                        'email': 'sdpygl@gmail.com',
                        'likeCount': 10,
                        "created": "2019-08-24T14:15:22Z",
                        "updated": "2019-08-24T14:15:22Z",
                        'commentCount': 10,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.PostListFilterSerializer(
            data=request.query_params)
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
            serializer_class=self.PostListOutputSerializer,
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
    class PostDetailOutputSerializer(serializers.Serializer):
        board = serializers.IntegerField()
        title = serializers.CharField()
        content = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()

        likeCount = serializers.IntegerField()
        viewCount = serializers.IntegerField()
        likes = serializers.BooleanField()

        # 게시판 지원 기능에 따라 전달 여부 결정되는 필드
        hashtagList = serializers.ListField(required=False)
        photoList = serializers.ListField(required=False)

    @swagger_auto_schema(
        operation_id='커뮤니티 게시글 조회',
        operation_description='''
                전달된 id에 해당하는 게시글 디테일을 조회합니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'board': 1,
                        'title': '안녕 상점 추천합니다.',
                        'content': '개인적으로 좋았습니다.',
                        'nickname': 'sdpygl',
                        'email': 'sdpygl@gmail.com',
                        "created": "2019-08-24T14:15:22Z",
                        "updated": "2019-08-24T14:15:22Z",

                        'likeCount': 10,
                        'viewCount': 100,
                        'likes': False,

                        'hashtagList': ['안녕', '상점'],
                        'photoList': ['https://abc.com/1.jpg', 'https://abc.com/2.jpg'],
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request, post_id):
        selector = PostCoordinatorSelector(
            user=request.user
        )
        post = selector.detail(
            post_id=post_id)

        serializer = self.PostDetailOutputSerializer(post)

        return Response(serializer.data)


class PostHashtagListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    class PostHashtagListFilterSerializer(serializers.Serializer):
        board = serializers.IntegerField(required=True)
        query = serializers.CharField(required=True)

    class PostHashtagListOutputSerializer(serializers.Serializer):
        name = serializers.CharField()
        postCount = serializers.IntegerField()

    # ref. https://stackoverflow.com/questions/55007336/drf-yasg-customizing
    @swagger_auto_schema(
        query_serializer=PostHashtagListFilterSerializer,
        responses={
            '200': PostHashtagListOutputSerializer,
            '400': 'Bad Request'
        },
        security=[],
        operation_id='커뮤니티 게시글 해시태그 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 게시글 해시태그 리스트를 반환합니다.<br/>
        ''',
    )
    def get(self, request):
        filters_serializer = self.PostHashtagListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = PostHashtagSelector()
        hashtags = selector.list(
            board_id=filters['board'],
            query=filters['query']  # 해당 검색어로 시작하는 모든 해시태그 리스트
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.PostHashtagListOutputSerializer,
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
