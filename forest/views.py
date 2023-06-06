from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from core.views import get_paginated_response
from .services import ForestCoordinatorService, ForestPhotoService, ForestService
from .selectors import ForestSelector, CategorySelector
from .permissions import IsWriter
from .models import Forest


class ForestCreateApi(APIView):
    permission_classes = (IsAuthenticated, )

    class ForestCreateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        subtitle = serializers.CharField()
        content = serializers.CharField()
        category = serializers.CharField()
        semi_categories = serializers.ListField()

        hashtags = serializers.ListField(required=False)
        photos = serializers.ListField(required=False)

        class Meta:
            examples = {
                'title': '신재생에너지 종류 “풍력에너지 개념/특징/국내외 현황”',
                'subtitle': '풍력발전이란? 풍력 발전은 바람이 가진 운동에너지를 변환하여 전기 에너지를 생산',
                'content': '육상에 설치된 풍력발전기를 육상풍력발전기, 해상에 설치된 풍력발전기를',
                'category': '1',
                'semi_categories': ["add,1", "add,2"],
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
        hashtags = serializers.ListField(required=False)
        photos = serializers.ListField(required=False)

        class Meta:
            examples = {
                'title': '신재생에너지 종류 “풍력에너지 개념/특징/국내외 현황”',
                'subtitle': '풍력발전이란? 풍력 발전은 바람이 가진 운동에너지를 변환하여 전기 에너지를 생산',
                'content': '육상에 설치된 풍력발전기를 육상풍력발전기, 해상에 설치된 풍력발전기를',
                'category': '1',
                'semi_categories': ["remove,2"],
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
        category = serializers.CharField()
        semi_categories = serializers.ListField()
        hashtags = serializers.ListField()
        rep_pic = serializers.CharField()
        writer_nickname = serializers.CharField()
        writer_profile = serializers.CharField()
        writer_is_verified = serializers.BooleanField()
        user_likes = serializers.BooleanField()
        like_cnt = serializers.IntegerField()
        created = serializers.DateTimeField()

    @swagger_auto_schema(
        operation_id='포레스트 글 디테일 조회',
        operation_description='''
            전달된 id에 해당하는 포레스트 글 디테일을 조회합니다.<br/>
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
                        'category': '시사',
                        'semi_categories': ['기업'],
                        'hashtags': ['풍력발전', '신재생에너지'],
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_is_verified': True,
                        'writer_nickname': 'sdp_official',
                        'writer_profile': 'https://abc.com/1.jpg',
                        'user_likes': True,
                        'like_cnt': 1,
                        "created": "2023-06-06T23:59:43.595632+09:00",
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

    class ForestListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        subtitle = serializers.CharField()
        preview = serializers.CharField()
        rep_pic = serializers.CharField()
        writer_nickname = serializers.CharField()
        writer_is_verified = serializers.BooleanField()
        user_likes = serializers.BooleanField()
        like_cnt = serializers.IntegerField()
        created = serializers.DateTimeField()

    @swagger_auto_schema(
        operation_id='포레스트 글 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 포레스트 글 리스트를 반환합니다.<br/>
            <br/>
            search : title, subtitle, content 내 검색어<br/>
            order : 정렬 기준(latest, hot)<br/>
            category_filter: 카테고리 id <br/>
            semi_category_filter: 세미 카테고리 id 리스트 <br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '신재생에너지 종류 “풍력에너지 개념/특징/국내외 현황”',
                        'subtitle': '풍력발전이란? 풍력 발전은 바람이 가진 운동에너지를 변환하여 전기 에너지를 생산',
                        'preview': '육상에 설치된 풍력발전기를 육상풍력발전기, 해상에 설치된 풍력발전기를',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_is_verified': True,
                        'writer_nickname': 'sdp_official',
                        'writer_profile': 'https://abc.com/1.jpg',
                        'user_likes': True,
                        'like_cnt': 1,
                        "created": "2023-06-06T23:59:43.595632+09:00",
                    },
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
