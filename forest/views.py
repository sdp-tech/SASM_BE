from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from core.views import get_paginated_response
from .services import ForestCoordinatorService, ForestPhotoService, ForestService, ForestCommentService, ForestUserCategoryService
from .selectors import ForestSelector, CategorySelector, ForestCommentSelector
from .permissions import IsWriter
from .models import Forest, ForestComment
from users.serializers import UserSerializer


class ForestCreateApi(APIView):
    permission_classes = (IsAuthenticated, )

    class ForestCreateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        subtitle = serializers.CharField()
        content = serializers.CharField()
        category = serializers.CharField()
        semi_categories = serializers.ListField()
        rep_pic = serializers.ImageField()

        hashtags = serializers.ListField(required=False)
        photos = serializers.ListField(required=False)

        class Meta:
            examples = {
                'title': '신재생에너지 종류 “풍력에너지 개념/특징/국내외 현황”',
                'subtitle': '풍력발전이란? 풍력 발전은 바람이 가진 운동에너지를 변환하여 전기 에너지를 생산',
                'content': '육상에 설치된 풍력발전기를 육상풍력발전기, 해상에 설치된 풍력발전기를',
                'category': '1',
                'semi_categories': ["add,1", "add,2"],
                'rep_pic': '<IMAGE FILE>',
                'hashtags': ["add,신재생에너지", "add,풍력에너지"],
                'photos': ["add,https://sasm-bucket.s3.amazonaws.com/media/forest/post/1686065590.jpg", "add,https://sasm-bucket.s3.amazonaws.com/media/forest/post/1686065590.jpg"],
            }

    @swagger_auto_schema(
        request_body=ForestCreateInputSerializer,
        operation_id='포레스트 글 생성',
        operation_description='''
            전달된 필드값을 기반으로 포레스트 글을 생성합니다.<br/>
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
        serializer = self.ForestCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        forest = ForestCoordinatorService.create(
            title=data.get('title'),
            subtitle=data.get('subtitle'),
            content=data.get('content'),
            category=data.get('category'),
            semi_categories=data.get('semi_categories', []),
            rep_pic=data.get('rep_pic'),
            hashtags=data.get('hashtags', []),
            photos=data.get('photos', []),
            writer=request.user,
        )

        return Response({
            'status': 'success',
            'data': {'id': forest.id},
        }, status=status.HTTP_201_CREATED)


class ForestUpdateApi(APIView):
    permission_classes = (IsWriter, )

    class ForestUpdateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        subtitle = serializers.CharField()
        content = serializers.CharField()
        category = serializers.CharField()
        semi_categories = serializers.ListField(required=False)
        rep_pic = serializers.ImageField(required=False)
        hashtags = serializers.ListField(required=False)
        photos = serializers.ListField(required=False)

        class Meta:
            examples = {
                'title': '신재생에너지 종류 “풍력에너지 개념/특징/국내외 현황”',
                'subtitle': '풍력발전이란? 풍력 발전은 바람이 가진 운동에너지를 변환하여 전기 에너지를 생산',
                'content': '육상에 설치된 풍력발전기를 육상풍력발전기, 해상에 설치된 풍력발전기를',
                'category': '1',
                'semi_categories': ["remove,2"],
                'rep_pic': '<IMAGE FILE>',
                'hashtags': ["remove,풍력에너지", "add,풍력발전"],
                'photos': ["remove,https://sasm-bucket.s3.amazonaws.com/media/forest/post/1686065590.jpg", "add,https://sasm-bucket.s3.amazonaws.com/media/forest/post/1686065590.jpg"],
            }

    @swagger_auto_schema(
        request_body=ForestUpdateInputSerializer,
        operation_id='포레스트 글 업데이트',
        operation_description='''
            전달된 필드값을 기반으로 포레스트 글을 수정합니다.<br/>
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
    def patch(self, request, forest_id):
        serializer = self.ForestUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        forest = ForestCoordinatorService.update(
            forest=get_object_or_404(Forest, pk=forest_id),
            title=data.get('title'),
            subtitle=data.get('subtitle'),
            content=data.get('content'),
            category=data.get('category'),
            semi_categories=data.get('semi_categories', []),
            rep_pic=data.get('rep_pic', None),
            hashtags=data.get('hashtags', []),
            photos=data.get('photos', []),
        )

        return Response({
            'status': 'success',
            'data': {'id': forest.id},
        }, status=status.HTTP_200_OK)


class ForestDeleteApi(APIView):
    permission_classes = (IsWriter, )

    @swagger_auto_schema(
        operation_id='포레스트 글 삭제',
        operation_description='''
            전달된 id를 가지는 포레스트 글을 삭제합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        }
    )
    def delete(self, request, forest_id):
        ForestCoordinatorService.delete(
            forest=get_object_or_404(Forest, pk=forest_id),
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class ForestPhotoCreateApi(APIView):
    permission_classes = (IsAuthenticated, )

    class ForestPhotoCreateInputSerializer(serializers.Serializer):
        image = serializers.ImageField()

        class Meta:
            examples = {
                'image': '<IMAGE BINARY>',
            }

    @swagger_auto_schema(
        request_body=ForestPhotoCreateInputSerializer,
        operation_id='포레스트 글 첨부 사진 업로드',
        operation_description='''
            포레스트 글에 첨부될 사진을 업로드합니다. 업로드 결과로 이미지 URL이 반환됩니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"location": "https://sasm-bucket.s3.amazonaws.com/media/forest/post/1686065590.jpg"}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
        serializer = self.ForestPhotoCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        forest_photo_url = ForestPhotoService.create(
            image=data.get('image'),
        )

        return Response({
            'status': 'success',
            'data': {'location': forest_photo_url},
        }, status=status.HTTP_201_CREATED)


class ForestLikeApi(APIView):
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(
        operation_id='포레스트 글 좋아요 또는 좋아요 취소',
        operation_description='''
            입력한 id를 가지는 포레스트 글에 대한 사용자의 좋아요/좋아요 취소를 수행합니다.<br/>
            결과로 좋아요 상태(TRUE:좋아요, FALSE:좋아요X)가 반환됩니다.
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
    def post(self, request, forest_id):
        likes = ForestService.like_or_dislike(
            forest=get_object_or_404(Forest, pk=forest_id),
            user=request.user
        )

        return Response({
            'status': 'success',
            'data': {'likes': likes},
        }, status=status.HTTP_200_OK)


class ForestDetailApi(APIView):
    permission_classes = (AllowAny, )

    class ForestDetailOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        subtitle = serializers.CharField()
        content = serializers.CharField()
        category = serializers.DictField()
        semi_categories = serializers.ListField()
        rep_pic = serializers.CharField()
        hashtags = serializers.ListField()
        photos = serializers.ListField()
        writer = serializers.DictField()
        user_likes = serializers.BooleanField()
        like_cnt = serializers.IntegerField()
        comment_cnt = serializers.IntegerField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()
        writer_is_followed = serializers.BooleanField()

    @swagger_auto_schema(
        operation_id='포레스트 글 디테일 조회',
        operation_description='''
            전달된 id에 해당하는 포레스트 글 디테일을 조회합니다.<br/>
            photos 배열 중 0번째 원소가 대표 이미지(rep_pic)입니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '신재생에너지 종류 “풍력에너지 개념/특징/국내외 현황”',
                        'subtitle': '풍력발전이란? 풍력 발전은 바람이 가진 운동에너지를 변환하여 전기 에너지를 생산',
                        'content': '육상에 설치된 풍력발전기를 육상풍력발전기, 해상에 설치된 풍력발전기를',
                        'category': {
                            'id': 1,
                            'name': '시사'
                        },
                        'semi_categories': [
                            {
                                'id': 1,
                                'name': '테크놀리지'
                            }
                        ],
                        'rep_pic': "https://sasm-bucket.s3.amazonaws.com/media/forest/rep_pic/abc.jpg",
                        'hashtags': ['풍력발전', '신재생에너지'],
                        'photos': [
                            "https://sasm-bucket.s3.amazonaws.com/media/forest/post/1687078027.978057749349c6c5de4fe59771223b9b47e8c8.jpg",
                            "https://sasm-bucket.s3.amazonaws.com/media/forest/post/1687078087.49140690310232dc94437786446deb035592ac.jpg"
                        ],
                        "writer": {
                            "email": "sdpygl@gmail.com",
                            "nickname": "sdp_offical",
                            "profile": "https://sasm-bucket.s3.amazonaws.com/media/profile/20230401/abc.jpg",
                            "is_verified": False,
                            "writer_is_followed" : True, 
                        },
                        'user_likes': True,
                        'like_cnt': 1,
                        "created": "2023-06-18T08:49:12+0000",
                        "updated": "2023-06-18T08:49:12+0000"
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request, forest_id):
        forest = ForestSelector.detail(forest_id=forest_id,
                                       user=request.user)

        serializer = self.ForestDetailOutputSerializer(forest)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class ForestListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    class ForestListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        order = serializers.CharField(required=False)
        category_filter = serializers.CharField(required=False)
        semi_category_filters = serializers.ListField(required=False)
        writer_filter = serializers.CharField(required=False)

    class ForestListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        subtitle = serializers.CharField()
        preview = serializers.CharField()
        rep_pic = serializers.CharField()
        photos = serializers.ListField()
        writer = serializers.DictField()
        user_likes = serializers.BooleanField()
        like_cnt = serializers.IntegerField()
        comment_cnt = serializers.IntegerField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()
        semi_categories = serializers.ListField(child=serializers.DictField())

    @swagger_auto_schema(
        query_serializer=ForestListFilterSerializer,
        operation_id='포레스트 글 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 포레스트 글 리스트를 반환합니다.<br/>
            photos 배열 중 0번째 원소가 대표 이미지(rep_pic)입니다.<br/>
            <br/>
            search : title, subtitle, content 내 검색어<br/>
            order : 정렬 기준(latest, hot)<br/>
            category_filter: 카테고리 id <br/>
            semi_category_filter: 세미 카테고리 id 리스트 <br/>
            writer_filter: 작성자 email <br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "count": 1,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "id": 1,
                                    'title': '신재생에너지 종류 “풍력에너지 개념/특징/국내외 현황”',
                                    'subtitle': '풍력발전이란? 풍력 발전은 바람이 가진 운동에너지를 변환하여 전기 에너지를 생산',
                                    'preview': '육상에 설치된 풍력발전기를 육상풍력발전기, 해상에 설치된 풍력발전기를',
                                    'rep_pic': "https://sasm-bucket.s3.amazonaws.com/media/forest/rep_pic/abc.jpg",
                                    "photos": [
                                        "https://sasm-bucket.s3.amazonaws.com/media/forest/post/1687078027.978057749349c6c5de4fe59771223b9b47e8c8.jpg",
                                        "https://sasm-bucket.s3.amazonaws.com/media/forest/post/1687078087.49140690310232dc94437786446deb035592ac.jpg"
                                    ],
                                    "writer": {
                                        "email": "sdpygl@gmail.com",
                                        "nickname": "sdp_official",
                                        "profile": 'https://abc.com/1.jpg',
                                        "is_verified": False
                                    },
                                    "user_likes": True,
                                    "like_cnt": 0,
                                    "created": "2023-06-18T08:49:12+0000",
                                    "updated": "2023-06-18T08:49:12+0000",
                                    "semi_categories": [
                                        {
                                            "id": 1, 
                                            "name": "semi category 1"
                                        },
                                        {
                                            "id": 2, 
                                            "name": "semi category 2"
                                        }
                                    ],                   
                                },
                            ]
                        }
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.ForestListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        forests = ForestSelector.list(
            search=filters.get('search', ''),
            order=filters.get('order', 'latest'),
            category_filter=filters.get('category_filter', ''),
            semi_category_filters=filters.get('semi_category_filters', []),
            writer_filter=filters.get('writer_filter', ''),
            user=request.user,
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.ForestListOutputSerializer,
            queryset=forests,
            request=request,
            view=self
        )


class CategoryListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    class CategoryListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()

    @swagger_auto_schema(
        operation_id='카테고리 리스트',
        operation_description='''
            사용 가능한 카테고리 리스트를 반환합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'name': '시사',
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        categories = CategorySelector.category_list()

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.CategoryListOutputSerializer,
            queryset=categories,
            request=request,
            view=self
        )


class SemiCategoryListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    class SemiCategoryListFilterSerializer(serializers.Serializer):
        category = serializers.CharField()

    class SemiCategoryListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()

    @swagger_auto_schema(
        query_serializer=SemiCategoryListFilterSerializer,
        operation_id='세미 카테고리 리스트',
        operation_description='''
            사용 가능한 세미 카테고리 리스트를 반환합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'name': '테크놀로지',
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.SemiCategoryListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        categories = CategorySelector.semi_category_list(
            category=filters.get('category'))

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.SemiCategoryListOutputSerializer,
            queryset=categories,
            request=request,
            view=self
        )


class ForestCommentListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 20
        page_size_query_param = 'page_size'

    class ForestCommentListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        content = serializers.CharField()
        like_cnt = serializers.IntegerField()
        writer = serializers.DictField()
        user_likes = serializers.BooleanField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()

    @swagger_auto_schema(
        operation_id='포레스트 글 댓글 조회',
        operation_description='''
            해당 포레스트 글의 하위 댓글을 조회합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "count": 1,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    'id': 1,
                                    'content': '정말 재미있어 보이는 장소네요 ~! 근처에 가게 되면 꼭 한 번 방문해보고 싶네요 ㅎㅎ 저장해두겠습니다 ~~ ',
                                    'like_cnt': 10,
                                    "writer": {
                                        "email": "sdpygl@gmail.com",
                                        "nickname": "sdpygl",
                                        "profile": "https://abc.com/1.jpg",
                                        "is_verified": False
                                    },
                                    "user_likes": True,
                                    "created": "2023-06-07T13:44:44+0000",
                                    "updated": "2023-06-07T13:45:31+0000"
                                }
                            ]
                        }
                    }
                },
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request, forest_id):
        forest_comments = ForestCommentSelector.list(
            forest=get_object_or_404(Forest, pk=forest_id),
            user=request.user,
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.ForestCommentListOutputSerializer,
            queryset=forest_comments,
            request=request,
            view=self,
        )


class ForestCommentCreateApi(APIView):
    permission_classes = (IsAuthenticated, )

    class ForestCommentCreateInputSerializer(serializers.Serializer):
        content = serializers.CharField()

        class Meta:
            examples = {
                'content': '정말 재미있어 보이는 장소네요 ~! 근처에 가게 되면 꼭 한 번 방문해보고 싶네요 ㅎㅎ 저장해두겠습니다 ~~ ',
            }

    @swagger_auto_schema(
        request_body=ForestCommentCreateInputSerializer,
        security=[],
        operation_id='포레스트 글 댓글 생성',
        operation_description='''
            전달된 필드를 기반으로 해당 포레스트 글의 댓글을 생성합니다.<br/>
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
    def post(self, request, forest_id):
        serializer = self.ForestCommentCreateInputSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        forest_comment = ForestCommentService.create(
            forest=get_object_or_404(Forest, pk=forest_id),
            content=data.get('content'),
            writer=request.user
        )

        return Response({
            'status': 'success',
            'data': {'id': forest_comment.id},
        }, status=status.HTTP_201_CREATED)


class ForestCommentUpdateApi(APIView):
    permission_classes = (IsWriter, )

    class ForestCommnetUpdateInputSerializer(serializers.Serializer):
        content = serializers.CharField()

        class Meta:
            examples = {
                'content': '정말 재미있어 보이는 장소네요 ~! 근처에 가게 되면 꼭 한 번 방문해보고 싶네요 ㅎㅎ 저장해두겠습니다 ~~ ',
            }

    @swagger_auto_schema(
        request_body=ForestCommnetUpdateInputSerializer,
        security=[],
        operation_id='포레스트 글 댓글 수정',
        operation_description='''
            전달된 id에 해당하는 댓글을 업데이트합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                    }
                },
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def put(self, request, forest_id, forest_comment_id):
        serializers = self.ForestCommnetUpdateInputSerializer(
            data=request.data)
        serializers.is_valid(raise_exception=True)
        data = serializers.validated_data

        ForestCommentService.update(
            forest_comment=get_object_or_404(
                ForestComment, pk=forest_comment_id),
            content=data.get('content'),
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class ForestCommentDeleteApi(APIView):
    permission_classes = (IsWriter, )

    @swagger_auto_schema(
        operation_id='포레스트 글 댓글 삭제',
        operation_description='''
            전달받은 id에 해당하는 포레스트 글 댓글을 삭제합니다<br/>
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
    def delete(self, request, forest_id, forest_comment_id):
        ForestCommentService.delete(
            forest_comment=get_object_or_404(
                ForestComment, pk=forest_comment_id),
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class ForestCommentLikeApi(APIView):
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(
        operation_id='포레스트 글 댓글 좋아요 또는 좋아요 취소',
        operation_description='''
            입력한 id를 가지는 포레스트 글 댓글에 대한 사용자의 좋아요/좋아요 취소를 수행합니다.<br/>
            결과로 좋아요 상태(TRUE:좋아요, FALSE:좋아요X)가 반환됩니다.
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
    def post(self, request, forest_id, forest_comment_id):
        likes = ForestCommentService.like_or_dislike(
            forest_comment=get_object_or_404(
                ForestComment, pk=forest_comment_id),
            user=request.user
        )

        return Response({
            'status': 'success',
            'data': {'likes': likes},
        }, status=status.HTTP_200_OK)


class ForestReportApi(APIView):
    permission_classes = (IsAuthenticated, )

    class ForestReportCreateInputSerializer(serializers.Serializer):
        category = serializers.CharField()

        class Meta:
            examples = {
                'category': '지나친 광고성 컨텐츠입니다.(상업적 홍보)'
            }

    @swagger_auto_schema(
        security=[],
        operation_id='포레스트 게시글 신고',
        operation_description='''
            포레스트 게시글을 신고합니다.<br/>
            category로 가능한 값은 아래와 같습니다.<br/>
            1. "지나친 광고성 컨텐츠입니다.(상업적 홍보)"
            2. "욕설이 포함된 컨텐츠입니다."
            3. "성희롱이 포함된 컨텐츠입니다."
            <br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request, forest_id):
        serializer = self.ForestReportCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ForestService.report(
            forest=get_object_or_404(Forest, pk=forest_id),
            report_category=data.get('category'),
            reporter=request.user
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_201_CREATED)
    

class ForestUserCategoryApi(APIView):
    permission_classes = (IsAuthenticated, )


    class ForestUserCategoryInputSerializer(serializers.Serializer):
        semi_categories = serializers.ListField()

        class Meta:
            examples ={
                'semi_categories' : ['1','2','3']
            }

    @swagger_auto_schema(
        request_body=ForestUserCategoryInputSerializer,
        operation_id='나만의 카테고리 저장',
        operation_description='''
            전달된 세미카테고리 id 값을 기반으로 유저가 선택한 나만의 카테고리 id 리스트를 저장합니다.
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json":{
                        "status": 'success',
                        "id": 1,
                        "gender": "male",
                        "nickname": "sdpofficial",
                        "birthdate": "2000.03.12",
                        "email": "sdptech@gmail.com",
                        "address": "서대문구 연세로",
                        "profile_image": "https://abc.com/1.jpg",
                        "is_sdp_admin": 'true',
                        "is_verified": 'false',
                        "introduction": "안녕하세요",
                        'semi_categories': ['1','2','3']
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
         serializer = self.ForestUserCategoryInputSerializer(data = request.data, partial=True)
         serializer.is_valid(raise_exception=True)
         data = serializer.validated_data

         service = ForestUserCategoryService(user=request.user)

         semi_category = service.save_usercategory(
             semi_categories=data.get('semi_categories', None),
         )

         user_serializer = UserSerializer(semi_category)

         return Response({
             'status':'success',
             'data' :  user_serializer.data

         },status=status.HTTP_200_OK)