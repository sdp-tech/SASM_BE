import time
import uuid

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from stories.selectors import StoryCoordinatorSelector, StorySelector, semi_category, StoryLikeSelector, MapMarkerSelector, StoryCommentSelector
from stories.services import StoryCoordinatorService, StoryCommentCoordinatorService, StoryPhotoService
from core.views import get_paginated_response
from core.permissions import IsVerifiedOrSdpStaff

from .models import Story, StoryComment
from .selectors import StoryLikeSelector
from .permissions import IsWriter
from users.models import User
from places.serializers import MapMarkerSerializer
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class StoryCreateApi(APIView):
    permission_classes = (IsVerifiedOrSdpStaff, )

    class StoryCreateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        place = serializers.IntegerField()
        story_review = serializers.CharField()
        tag = serializers.CharField()
        preview = serializers.CharField()
        html_content = serializers.CharField()
        rep_pic = serializers.ImageField()
        photoList = serializers.ListField(required=False)

        def change_rep_pic_name(self, story, validated_data):
            place_name = validated_data['place'].place_name
            ext = story.rep_pic.name.split(".")[-1]
            story.rep_pic.name = '{}/{}.{}'.format(place_name,
                                                   'rep' + str(time.time())+str(uuid.uuid4().hex), ext)

        class Meta:
            examples = {
                'title': '매력적인 편집샵, 지구샵',
                'place': '지구샵 제로웨이스트홈',
                'preview': '지구샵으로 초대합니다.',
                'tag': '#환경친화적 #제로웨이스트',
                'story_review': '빈손으로는 나올 수 없는 제로웨이스트 샵',
                'html_content': '망원동, 성수, 연남동을 지나가는 걸음을 멈추게 하는 곳, 편집샵에 가 본 적이 있는가?...',
                'rep_pic': 'https://abc.com/2.jpg',
                'photoList': "['https://abc.com/1.jpg', 'https://abc.com/2.jpg', 'https://abc.com/3.jpg']"
            }

    @swagger_auto_schema(
        request_body=StoryCreateInputSerializer,
        operation_id='스토리 게시글 생성',
        operation_description='''
            전달된 필드를 기반으로 스토리 게시글을 생성합니다.<br/>
            photoList에는 Tinymce 등의 편집기 사용 시 스토리 생성 이전에 story_photos/create/을 통해 업로드된 이미지들의 주소를 포함하여야합니다.
            photoList에 해당 정보가 포함되어야 스토리와 스토리 포토 간 관계 매핑이 가능해집니다.
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
        serializer = self.StoryCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = StoryCoordinatorService(
            user=request.user
        )

        story = service.create(
            title=data.get('title'),
            writer=request.user,
            place_id=data.get('place'),
            preview=data.get('preview'),
            tag=data.get('tag'),
            story_review=data.get('story_review'),
            html_content=data.get('html_content'),
            rep_pic=data.get('rep_pic'),
            photoList=data.get('photoList', [])
        )

        return Response({
            'status': 'success',
            'data': {'id': story.id},
        }, status=status.HTTP_201_CREATED)


class StoryPhotoCreateApi(APIView):
    permission_classes = (IsVerifiedOrSdpStaff, )

    class StoryPhotoCreateInputSerializer(serializers.Serializer):
        image = serializers.ImageField()
        caption = serializers.CharField(required=False)
        place_id = serializers.IntegerField()

        class Meta:
            examples = {
                'image': '<IMAGE BINARY>',
                'caption': '내부 전경',
            }

    @swagger_auto_schema(
        request_body=StoryPhotoCreateInputSerializer,
        operation_id='스토리 사진 생성',
        operation_description='''
            스토리 사진을 생성합니다.<br/>
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
        serializer = self.StoryPhotoCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = StoryPhotoService()

        story_photo = service.create(
            caption=data.get('caption'),
            image=request.FILES['image'],
            place_id=data.get('place_id')
        )

        image_location = settings.MEDIA_URL + story_photo.image.name

        return Response({
            'status': 'success',
            'data': {'location': image_location},
        }, status=status.HTTP_201_CREATED)


class StoryListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class StoryListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        order = serializers.CharField(required=False)
        filter = serializers.ListField(required=False)

    class StoryListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        preview = serializers.CharField()
        rep_pic = serializers.CharField()
        extra_pics = serializers.ListField()
        views = serializers.IntegerField()
        story_like = serializers.SerializerMethodField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        semi_category = serializers.SerializerMethodField()
        writer = serializers.CharField()
        writer_is_verified = serializers.BooleanField()
        nickname = serializers.CharField()
        created = serializers.DateTimeField()

        def get_semi_category(self, obj):
            result = semi_category(obj.id)
            return result

        def get_story_like(self, obj):
            re_user = self.context['request'].user
            likes = StoryLikeSelector.likes(obj.id, user=re_user)
            return likes

    @swagger_auto_schema(
        operation_id='스토리 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 게시글 리스트를 반환합니다.<br/>
            <br/>
            search : 제목 혹은 장소 검색어<br/>
            latest : 최신순 정렬 여부 (ex: true)</br>
            array : 카테고리</br>
            ''',
        query_serializer=StoryListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'category': '녹색 공간',
                        'semi_category': '반려동물 출입 가능, 오보',
                        'preview': '서울숲. 가장 도시적인 단어...(최대 150자)',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'story_like': True,
                        'writer': 'sdptech@gmail.com',
                        'writer_is_verified': True,
                        'nickname': 'sdp_official',
                        'created': '2023-08-24T14:15:22Z',
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.StoryListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        story = StorySelector.list(
            search=filters.get('search', ''),
            order=filters.get('order', 'latest'),
            filter=filters.get('filter', []),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.StoryListOutputSerializer,
            queryset=story,
            request=request,
            view=self
        )


class StoryDetailApi(APIView):
    permission_classes = (AllowAny, )

    class StoryDetailOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        story_review = serializers.CharField()
        rep_pic = serializers.CharField()
        extra_pics = serializers.ListField()
        tag = serializers.CharField()
        html_content = serializers.CharField()
        story_like = serializers.BooleanField()
        views = serializers.IntegerField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        semi_category = serializers.CharField()
        writer = serializers.CharField()
        writer_is_verified = serializers.BooleanField()
        nickname = serializers.CharField()
        profile = serializers.CharField()
        created = serializers.DateTimeField()  # 게시글 생성 날짜
        map_image = serializers.CharField()

    @swagger_auto_schema(
        operation_id='스토리 글 조회',
        operation_description='''
            전달된 id에 해당하는 스토리 디테일을 조회합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'category': '녹색 공간',
                        'semi_category': '반려동물 출입 가능, 텀블러 사용 가능, 비건',
                        'tag': '#생명 다양성 #자연 친화 #함께 즐기는',
                        'story_review': '"모두에게 열려있는 도심 속 가장 자연 친화적인 여가공간"',
                        'html_content': '서울숲. 가장 도시적인 단어...(최대 150자)',
                        'views': 45,
                        'story_like': True,
                        'writer': 'sdptech@gmail.com',
                        'writer_is_verified': True,
                        'nickname': 'sdp_official',
                        'profile': 'https://abc.com/1.jpg',
                        "created": "2023-08-24T14:15:22Z",
                        'map_image': 'https://abc.com/1.jpg',
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request, story_id):
        selector = StoryCoordinatorSelector(
            user=request.user
        )
        story = selector.detail(story_id=story_id)

        serializer = self.StoryDetailOutputSerializer(story)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class StoryUpdateApi(APIView):
    permission_classes = (IsWriter, )

    def get_story_object(self, story_id):
        story = get_object_or_404(Story, pk=story_id)
        self.check_object_permissions(self.request, story)
        return story

    class StoryUpdateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        story_review = serializers.CharField()
        tag = serializers.CharField()
        preview = serializers.CharField()
        html_content = serializers.CharField()
        rep_pic = serializers.ImageField()
        photoList = serializers.ListField(required=False)

    @swagger_auto_schema(
        request_body=StoryUpdateInputSerializer,
        security=[],
        operation_id='스토리 게시글 업데이트',
        operation_description='''
            전송된 모든 필드 값을 그대로 게시글에 업데이트하므로, 게시글에 포함되어야 하는 모든 필드 값이 request body에 포함되어야합니다.<br/>
            즉, 값이 수정된 필드뿐만 아니라 값이 그대로 유지되어야하는 필드도 함께 전송되어야합니다.<br/>
            photoList에는 Tinymce 등의 편집기 사용 시 스토리 업데이트 이전에 story_photos/create/을 통해 새롭게 업로드된 이미지들의 주소를 포함하여야합니다.
            이번 업데이트에서 새롭게 추가된 이미지들의 주소만 포함하면 되며, 이전 생성이나 업데이트 시 추가된 이미지 주소는 포함하지 않아도 됩니다.
            photoList에 해당 정보가 포함되어야 스토리와 스토리 포토 간 관계 매핑이 가능해집니다.
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
        }
    )
    def put(self, request, story_id):
        serializer = self.StoryUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        story = self.get_story_object(story_id)
        service = StoryCoordinatorService(
            user=request.user
        )

        story = service.update(
            story=story,
            title=data.get('title'),
            story_review=data.get('story_review'),
            tag=data.get('tag'),
            preview=data.get('preview'),
            html_content=data.get('html_content'),
            rep_pic=data.get('rep_pic'),
            photoList=data.get('photoList'),
        )

        return Response({
            'status': 'success',
            'data': {story.id},
        }, status=status.HTTP_200_OK)


class StoryDeleteApi(APIView):
    permission_classes = (IsWriter, )

    def get_story_object(self, story_id):
        story = get_object_or_404(Story, pk=story_id)
        self.check_object_permissions(self.request, story)
        return story

    @swagger_auto_schema(
        operation_id='스토리 게시글 삭제',
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
        }
    )
    def delete(self, request, story_id):
        story = self.get_story_object(story_id)

        service = StoryCoordinatorService(
            user=request.user
        )
        service.delete(
            story=story
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class StoryRecommendApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class StoryRecommendListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        created = serializers.DateTimeField()
        writer = serializers.CharField()
        writer_is_verified = serializers.BooleanField()

    @swagger_auto_schema(
        operation_id='story의 category와 같은 스토리 추천 리스트',
        operation_description='''
            해당 스토리의 category와 같은 스토리 리스트를 반환합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'writer': 'sdptech@gmail.com',
                        'writer_is_verified': True,
                        'created': '2023-08-24T14:15:22Z',
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        recommend_story = StorySelector.recommend_list(
            story_id=request.query_params.get('id')
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.StoryRecommendListOutputSerializer,
            queryset=recommend_story,
            request=request,
            view=self
        )


class StoryLikeApi(APIView):
    permission_classes = (IsAuthenticated, )

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
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
        try:
            service = StoryCoordinatorService(
                user=request.user
            )
            story_like = service.like_or_dislike(
                story_id=request.data['id'],
            )
        except:  # TODO: 에러 발생 상황 명시하고 ApplicationError raise하기
            return Response({
                'status': 'fail',
                'message': '권한이 없거나 story가 존재하지 않습니다.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'status': 'success',
            'data': {'story_like': story_like},
        }, status=status.HTTP_201_CREATED)


class BasicPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'


class GoToMapApi(APIView):
    permission_classes = (AllowAny, )

    @swagger_auto_schema(
        operation_id='스토리의 해당 장소로 Map 연결',
        operation_description='''
            전달받은 id에 해당하는 스토리의 장소로 Map을 연결해준다<br/>
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
    def get(self, request):
        selector = MapMarkerSelector(user=request.user)
        place = selector.map(story_id=request.data['id'])
        serializer = MapMarkerSerializer(place)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class StoryCommentListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 20
        page_size_query_param = 'page_size'

    class StoryCommentListFilterSerializer(serializers.Serializer):
        story = serializers.IntegerField(required=True)

    class StoryCommentListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        story = serializers.IntegerField()
        content = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        mention = serializers.CharField()
        profile_image = serializers.ImageField()
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField()

    @swagger_auto_schema(
        operation_id='스토리 댓글 조회',
        operation_description='''
            해당 story의 하위 댓글을 조회합니다.<br/>
        ''',
        query_serializer=StoryCommentListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'content': '멋져요',
                        'nickname': 'sdpygl',
                        'email': 'sdpygl@gmail.com',
                        'mention': 'sasm@gmail.com',
                        'profile_image': 'https://abc.com/1.jpg',
                        'created_at': '2019-08-24T14:15:22Z',
                        'updated_at': '2019-08-24T14:15:22Z',
                    }
                },
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.StoryCommentListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data
        selector = StoryCommentSelector()
        story_comments = selector.list(
            story_id=filters.get('story')  # story id값 받아서 넣기
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.StoryCommentListOutputSerializer,
            queryset=story_comments,
            request=request,
            view=self,
        )


class StoryCommentCreateApi(APIView):
    permission_classes = (IsAuthenticated, )

    class StoryCommentCreateInputSerializer(serializers.Serializer):
        story = serializers.IntegerField()
        content = serializers.CharField()
        mention = serializers.CharField(required=False)

        class Meta:
            examples = {
                'id': 1,
                'story': 1,
                'content': '정보 부탁드려요.',
                'mentionEmail': 'sdpygl@gmail.com',
            }

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
        serializer = self.StoryCommentCreateInputSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = StoryCommentCoordinatorService(
            user=request.user
        )
        story_comment = service.create(
            story_id=data.get('story'),
            content=data.get('content'),
            mentioned_email=data.get('mention', '')
        )

        return Response({
            'status': 'success',
            'data': {'id': story_comment.id},
        }, status=status.HTTP_200_OK)


class StoryCommentUpdateApi(APIView):
    permission_classes = (IsWriter, )

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
    def put(self, request, story_comment_id):
        story_comment = StoryComment.objects.get(id=story_comment_id)
        serializers = self.StoryCommnetUpdateInputSerializer(
            data=request.data)
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

        return Response({
            'status': 'success',
            'data': {'id': story_comment.id},
        }, status=status.HTTP_200_OK)


class StoryCommentDeleteApi(APIView):
    permission_classes = (IsWriter, )

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
        service = StoryCommentCoordinatorService(
            user=request.user
        )
        service.delete(
            story_comment_id=story_comment_id
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)
