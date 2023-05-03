from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework.views import APIView
from community.mixins import ApiAuthMixin, ApiNoAuthMixin
from community.services import PostCoordinatorService, PostCommentCoordinatorService, PostReportService, PostCommentReportService
from community.selectors import PostCoordinatorSelector, PostHashtagSelector, PostCommentCoordinatorSelector, BoardSelector

from .models import Post, PostComment
from .permissions import IsWriter
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

import traceback


class BoardPropertyDetailApi(ApiNoAuthMixin, APIView):
    class BoardPropertyDetailOutputSerializer(serializers.Serializer):
        name = serializers.CharField()
        supportsHashtags = serializers.BooleanField()
        supportsPostPhotos = serializers.BooleanField()
        supportsPostComments = serializers.BooleanField()
        supportsPostCommentPhotos = serializers.BooleanField()
        postContentStyle = serializers.CharField()

    @swagger_auto_schema(
        operation_id='커뮤니티 게시판(정보글에선 카테고리) 속성 조회',
        operation_description='''
                전달된 게시판 id에 해당하는 게시글 속성을 조회합니다.<br/>
                해당 게시판에 지정된 글양식이 없을 경우 null 값이 반환됩니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "name": "장소추천게시판",
                        "supportsHashtags": False,
                        "supportsPostPhotos": False,
                        "supportsPostComments": True,
                        "supportsPostCommentPhotos": False,
                        "postContentStyle": "장소명:\r\n추천 이유:\r\n기타:"
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request, board_id):
        board = BoardSelector.properties(board_id=board_id)

        serializer = self.BoardPropertyDetailOutputSerializer(board)

        return Response(serializer.data)


class PostCreateApi(ApiAuthMixin, APIView):
    class PostCreateInputSerializer(serializers.Serializer):
        board = serializers.IntegerField()
        title = serializers.CharField()
        content = serializers.CharField()
        hashtagList = serializers.ListField(required=False)
        imageList = serializers.ListField(required=False)

        # 정보글 관련 필드
        subtitle = serializers.CharField(required=False)
        keyword = serializers.CharField(required=False)
        places = serializers.ListField(required=False)

        class Meta:
            examples = {
                'board': 1,
                'title': '안녕 상점 추천합니다.',
                'content': '개인적으로 좋았습니다.',
                'hashtagList': ['안녕', '상점'],
                'imageList': ['<IMAGE FILE BINARY>', '<IMAGE FILE BINARY>'],
                'subtitle': '누구나 가기 편한 제로웨이스트샵',
                'keyword': '제로웨이스트',
                'places': [{"name": "안암 상점", "address": "서울특별시 성북구",
                            "contact": "010", "latitude": 37.101, "longitude": 37.101}]
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
                5. 시사 (정보글 카테고리) <br/>
            으로 설정되어 있습니다.<br/>
            개발을 위해 정보글 카테고리로 시사만 생성하고, 나머지는 아직 생성하지 않았습니다.<br/>
            <br/>
            hashtagList, imageList는 해당 게시판의 속성(게시글 해시태그 지원여부, 게시글 이미지 지원 여부 등)에 따라 선택적으로 포함될 수 있습니다.<br/>
            참고로 request body는 json 형식이 아닌 <b>multipart/form-data 형식</b>으로 전달받으므로, 리스트 값을 전달하고자 한다면 개별 원소들마다 리스트 필드 이름을 key로 설정하여, 원소 값을 value로 추가해주면 됩니다.<br/>
            가령 hashtagList의 경우, (key: 'hashtagList', value: '안녕'), (key: 'hashtagList', value: '상점') 과 같이 request body에 포함해주면 됩니다.<br/>
            <br/>
            정보글 전용 필드인 subtitle, keyword, places는 선택적으로 포함될 수 있습니다.<br/>
            subtitle은 소제목, keyword는 키워드, places는 장소 목록을 의미합니다.<br/>
            places는 place json 객체의 목록으로, {name, address, contact, latitude, longitude}를 가지는 json object를 stringify해서 원소로 추가해주면 됩니다.<br/>
            <br/>
            <정보글 카테고리 및 키워드 참고 자료><br/>
            시사: #테크놀리지, #기업, #정책 #ESG 관련 이슈 등<br/>
            액티비티: #박람회, #파머스마켓, #온라인행사, #전시, 지속가능성 관련 온/오프라인 행사 공유 (Eg. ‘비건페스타’ 3/15~ 개최) #리뷰<br/>
            라이프스타일: #친환경_생활용품, #그린_생활습관, #녹색_인테리어, #일상, #실천, #챌린지 등<br/>
            뷰티: #패션, #화장품 등<br/>
            푸드: #유기농_식자재, #건강식단_레시피 , #비건, #어린이식단 등(’맛집’과 다름)<br/>
            문화 컨텐츠: #베리어프리, #뮤지컬, #영화 #어플추천 #책 #매거진 #인플루언서 관련 주제를 다루는 온라인 플랫폼/앱, 책, 영화, 잡지, 영상, 잡지, SNS 등<br/>
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
        data = serializer.validated_data

        service = PostCoordinatorService(
            user=request.user
        )

        # request body가 json 방식이 아닌 multipart/form-data 방식으로 전달
        post = service.create(
            board_id=data.get('board'),
            title=data.get('title'),
            content=data.get('content'),
            hashtag_names=data.get('hashtagList', []),
            image_files=data.get('imageList', []),
            subtitle=data.get('subtitle', ''),
            keyword=data.get('keyword', ''),
            places=data.get('places', []),
        )

        return Response({
            'status': 'success',
            'data': {'id': post.id},
        }, status=status.HTTP_201_CREATED)


class PostUpdateApi(ApiAuthMixin, APIView):
    permission_classes = (IsWriter, )

    def get_object(self, post_id):
        post = get_object_or_404(Post, pk=post_id)
        self.check_object_permissions(self.request, post)
        return post

    class PostUpdateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        content = serializers.CharField()
        hashtagList = serializers.ListField(required=False)
        photoList = serializers.ListField(required=False)
        imageList = serializers.ListField(required=False)

        # 정보글 관련 필드
        subtitle = serializers.CharField(required=False)
        keyword = serializers.CharField(required=False)
        places = serializers.ListField(required=False)

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
             <br/>
            정보글 전용 필드인 subtitle, keyword, places는 선택적으로 포함될 수 있습니다.<br/>
            subtitle은 소제목, keyword는 키워드, places는 장소 목록을 의미합니다.
            places는 place json 객체의 목록으로, {name, address, contact, latitude, longitude}를 가지는 json object를 stringify해서 원소로 추가해주면 됩니다.
            places 사용 예시로, 정보글 디테일 API에서 전달받은 places 값(name 외 나머지 필드 생략)이 [{"name": "안암 상점"}, {"name": "신촌 상점"}] 일 때, 
            "안암 상점"을 지우고, "홍대 상점"을 새로 추가하고 싶다면 [{"name": "안암 상점"}, {"name": "홍대 상점"}]으로 값을 설정하면 됩니다.<br/>

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
        data = serializer.validated_data

        post = self.get_object(post_id)

        service = PostCoordinatorService(
            user=request.user
        )

        post = service.update(
            post=post,
            title=data.get('title'),
            content=data.get('content'),
            hashtag_names=data.get('hashtagList', []),
            photo_image_urls=data.get('photoList', []),
            image_files=data.get('imageList', []),
            subtitle=data.get('subtitle', ''),
            keyword=data.get('keyword', ''),
            places=data.get('places', []),
        )

        return Response({
            'status': 'success',
            'data': {'id': post.id},
        }, status=status.HTTP_200_OK)


class PostDeleteApi(ApiAuthMixin, APIView):
    permission_classes = (IsWriter, )

    def get_object(self, post_id):
        post = get_object_or_404(Post, pk=post_id)
        self.check_object_permissions(self.request, post)
        return post

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
        post = self.get_object(post_id)

        service = PostCoordinatorService(
            user=request.user
        )

        service.delete(
            post=post
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class PostLikeApi(ApiAuthMixin, APIView):
    def get_object(self, post_id):
        post = get_object_or_404(Post, pk=post_id)
        self.check_object_permissions(self.request, post)
        return post

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
        post = self.get_object(post_id)

        service = PostCoordinatorService(
            user=request.user
        )

        likes = service.like_or_dislike(
            post=post
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
        'data': paginator.get_paginated_response(serializer.data).data,
    }, status=status.HTTP_200_OK)


class PostListApi(ApiNoAuthMixin, APIView):
    class Pagination(PageNumberPagination):
        page_size = 5
        page_size_query_param = 'page_size'

    class PostListFilterSerializer(serializers.Serializer):
        board = serializers.CharField(required=True)
        query = serializers.CharField(required=False)
        query_type = serializers.CharField(required=False)
        latest = serializers.BooleanField(required=False)
        page = serializers.IntegerField(required=False)

        # # 정보글
        # query = serializers.CharField(required=False)
        # user_type = serializers.CharField(required=False)

    class PostListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        preview = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        likeCount = serializers.IntegerField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()

        # 게시판 지원 기능에 따라 전달 여부 결정되는 필드
        commentCount = serializers.IntegerField(required=False)

        # 정보글 관련 필드
        subtitle = serializers.CharField()
        keyword = serializers.CharField()
        # TODO: 대표이미지 지정 가능하도록 구현하기, 우선은 조회 시 첫번째 이미지로 반환
        rep_photo = serializers.CharField()

    @swagger_auto_schema(
        operation_id='커뮤니티 게시글 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 게시글 리스트를 반환합니다.<br/>
            <br/>
            query: 검색어 (ex: '지속가능성')</br>
            query_type: 검색 종류 (ex: 'default', 'hashtag')</br>
            latest: 최신순 정렬 여부 (ex: true)</br>
            keyword (정보글 전용): 키워드 </br>
            <br/>
            기본 검색의 경우, 전달된 query를 title, content, hashtags, comments.content에 포함하고 있는 게시글 리스트를 반환합니다.<br/>
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
                        'preview': '추천하고 싶은 이유는 ddsjfldksjflks....(최대 50자)',
                        'nickname': 'sdpygl',
                        'email': 'sdpygl@gmail.com',
                        'likeCount': 10,
                        "created": "2019-08-24T14:15:22Z",
                        "updated": "2019-08-24T14:15:22Z",
                        'commentCount': 10,
                        'subtitle': '누구나 가기 편한 제로웨이스트샵',
                        'keyword': '제로웨이스트',
                        'rep_photo': 'https://sasm-bucket.s3.amazonaws.com/media/comm~~'
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
            board_id=filters.get('board'),  # 게시판 id
            # 검색어
            query=filters.get('query', ''),
            # 검색어 종류 (해시태그 검색 여부)
            query_type=filters.get('query_type', 'default'),
            # 최신순 정렬 여부 (기본값: 최신순)
            latest=filters.get('latest', True),
            # 정보글 키워드
            keyword=filters.get('keyword', ''),
            # # 다른 정렬 옵션, 추후 latest를 order에 통합 예정
            # order=filters.get('order', 'latest'),
            # # 정보글 사용자 종류(관리자, 일반인)
            # user_type=filters.get('user_type', ''),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.PostListOutputSerializer,
            queryset=posts,
            request=request,
            view=self
        )


class PostDetailApi(ApiNoAuthMixin, APIView):
    class PostDetailOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        board = serializers.IntegerField()
        title = serializers.CharField()
        content = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        profile = serializers.CharField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()

        likeCount = serializers.IntegerField()
        viewCount = serializers.IntegerField()
        likes = serializers.BooleanField()

        # 게시판 지원 기능에 따라 전달 여부 결정되는 필드
        hashtagList = serializers.ListField(required=False)
        photoList = serializers.ListField(required=False)

        # 정보글 관련 필드
        subtitle = serializers.CharField()
        keyword = serializers.CharField()
        places = serializers.ListField()

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
                        'id': 12,
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

                        'subtitle': '누구나 가기 편한 제로웨이스트샵',
                        'keyword': '제로웨이스트',
                        'places': [{"name": "안암 상점", "address": "서울특별시 성북구",
                                    "contact": "010", "latitude": 37.101, "longitude": 37.101}]
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


class PostHashtagListApi(ApiNoAuthMixin, APIView):
    class Pagination(PageNumberPagination):
        page_size = 5
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
            board_id=filters.get('board'),
            query=filters.get('query')  # 해당 검색어로 시작하는 모든 해시태그 리스트
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.PostHashtagListOutputSerializer,
            queryset=hashtags,
            request=request,
            view=self
        )


class PostCommentListApi(ApiNoAuthMixin, APIView):
    class Pagination(PageNumberPagination):
        page_size = 20  # 미정
        page_size_query_param = 'page_size'

    class PostCommentListFilterSerializer(serializers.Serializer):
        post = serializers.IntegerField(required=True)
        query = serializers.CharField(required=False)
        query_type = serializers.CharField(required=False)
        latest = serializers.BooleanField(required=False)

    class PostCommentListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        content = serializers.CharField()
        isParent = serializers.BooleanField()
        group = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        mentionEmail = serializers.CharField()
        created = serializers.DateTimeField()
        updated = serializers.DateTimeField()
        photoList = serializers.ListField(required=False)

        # 정보글
        profile = serializers.CharField()

    @swagger_auto_schema(
        operation_id='커뮤니티 게시글 댓글 조회',
        operation_description='''
            해당 post의 하위 댓글을 반환합니다.<br/>
        ''',
        query_serializer=PostCommentListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 2,
                        'content': '저도 추천합니다.',
                        'isParent': True,
                        'group' "1"
                        'nickname': 'sdpygl',
                        'email': 'sdpygl@gmail.com',
                        'mentionEmail': 'ygl@gmail.com',
                        "created": "2019-08-24T14:15:22Z",
                        "updated": "2019-08-24T14:15:22Z"
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.PostCommentListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = PostCommentCoordinatorSelector(
            user=request.user
        )

        post_comments = selector.list(
            post_id=filters.get('post')
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.PostCommentListOutputSerializer,
            queryset=post_comments,
            request=request,
            view=self
        )


class PostCommentCreateApi(ApiAuthMixin, APIView):
    class PostCommentCreateInputSerializer(serializers.Serializer):
        post = serializers.IntegerField()
        content = serializers.CharField()
        isParent = serializers.BooleanField()
        parent = serializers.IntegerField(required=False)
        mentionEmail = serializers.CharField(required=False)
        # mentionNickname = serializers.CharField(required=False)
        imageList = serializers.ListField(required=False)

        class Meta:
            examples = {
                'post': 1,
                'content': '저도 방문했는데 좋았어요.',
                'isParent': True,
                'parent': 1,
                'mentionEmail': 'sdpygl@gmail.com',
                'imageList': ['<IMAGE FILE BINARY>', '<IMAGE FILE BINARY>'],
            }

    @swagger_auto_schema(
        request_body=PostCommentCreateInputSerializer,
        security=[],
        operation_id='커뮤니티 댓글 생성',
        operation_description='''
                전달된 필드를 기반으로 댓글을 생성합니다.<br/>
                imageList는 해당 게시판의 댓글 사진 지원 여부에 따라 선택적으로 포함될 수 있습니다.<br/>
                참고로 request body는 json 형식이 아닌 <b>multipart/form-data 형식</b>으로 전달받으므로, 리스트 값을 전달하고자 한다면 개별 원소들마다 리스트 필드 이름을 key로 설정하여, 원소 값을 value로 추가해주면 됩니다.<br/>          
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
        serializer = self.PostCommentCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = PostCommentCoordinatorService(
            user=request.user
        )

        # request body가 json 방식이 아닌 multipart/form-data 방식으로 전달
        post_comment = service.create(
            post_id=data.get('post'),
            content=data.get('content'),
            isParent=data.get('isParent'),
            parent_id=data.get('parent', None),
            mentioned_email=data.get('mentionEmail', ''),
            image_files=data.get('imageList', []),
        )

        return Response({
            'status': 'success',
            'data': {'id': post_comment.id},
        }, status=status.HTTP_201_CREATED)


class PostCommentUpdateApi(ApiAuthMixin, APIView):
    permission_classes = (IsWriter, )

    def get_object(self, post_comment_id):
        post_comment = get_object_or_404(PostComment, pk=post_comment_id)
        self.check_object_permissions(self.request, post_comment)
        return post_comment

    class PostCommentUpdateInputSerializer(serializers.Serializer):
        content = serializers.CharField()
        mentionEmail = serializers.CharField(required=False)
        # mentionNickname = serializers.CharField(required=False)
        photoList = serializers.ListField(required=False)
        imageList = serializers.ListField(required=False)

        class Meta:
            examples = {
                'content': '저도 어제 방문했는데 정말 좋았어요.',
                'mentionEmail': 'sdpygl3@gmail.com',
                'photoList': ['https://abc.com/2.jpg'],
                'imageList': ['<IMAGE FILE BINARY>', '<IMAGE FILE BINARY>'],
            }

    @swagger_auto_schema(
        request_body=PostCommentUpdateInputSerializer,
        security=[],
        operation_id='커뮤니티 댓글 업데이트',
        operation_description='''
                전달된 id에 해당하는 댓글을 업데이트합니다.<br/>
                전송된 모든 필드 값을 그대로 댓글에 업데이트하므로, 댓글에 포함되어야 하는 모든 필드 값이 request body에 포함되어야합니다.<br/>
                즉, 값이 수정된 필드뿐만 아니라 값이 그대로 유지되어야하는 필드도 함께 전송되어야합니다.<br/>
                <br/>
                photoList, imageList는 해당 게시판의 속성(게시글 이미지 지원 여부)에 따라 선택적으로 포함될 수 있습니다.<br/>
                photoList 사용 예시로, 게시글 디테일 API에서 전달받은 photoList 값이 ['https://abc.com/1.jpg', 'https://abc.com/2.jpg'] 일 때 '1.jpg'를 지우고 싶다면 ['https://abc.com/2.jpg'] 으로 값을 설정하면 됩니다.<br/>
                만약 새로운 photo를 추가하고 싶다면, imageList에 이미지 첨부 파일을 1개 이상 담아 전송하면 됩니다.<br/>
                <br/>
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
    def put(self, request, post_comment_id):
        post_comment = self.get_object(post_comment_id)

        serializer = self.PostCommentUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = PostCommentCoordinatorService(
            user=request.user
        )

        # request body가 json 방식이 아닌 multipart/form-data 방식으로 전달
        post_comment = service.update(
            post_comment=post_comment,
            content=data.get('content'),
            mentioned_email=data.get('mentionEmail', ''),
            photo_image_urls=data.get('photoList', []),
            image_files=data.get('imageList', []),
        )

        return Response({
            'status': 'success',
            'data': {'id': post_comment.id},
        }, status=status.HTTP_200_OK)


class PostCommentDeleteApi(ApiAuthMixin, APIView):
    permission_classes = (IsWriter, )

    def get_object(self, post_comment_id):
        post_comment = get_object_or_404(PostComment, pk=post_comment_id)
        self.check_object_permissions(self.request, post_comment)
        return post_comment

    @swagger_auto_schema(
        operation_id='커뮤니티 댓글 삭제',
        operation_description='''
                전달된 id에 해당하는 댓글을 삭제합니다.<br/>
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
    def delete(self, request, post_comment_id):
        post_comment = self.get_object(post_comment_id)

        service = PostCommentCoordinatorService(
            user=request.user
        )

        service.delete(
            post_comment=post_comment
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class PostReportCreateApi(ApiAuthMixin, APIView):
    class PostReportCreateInputSerializer(serializers.Serializer):
        post = serializers.IntegerField()
        category = serializers.CharField()

        class Meta:
            examples = {
                'post': 1,
                'category': '게시판 성격에 부적절함'
            }

    @swagger_auto_schema(
        request_body=PostReportCreateInputSerializer,
        security=[],
        operation_id='커뮤니티 게시글 신고내역 생성',
        operation_description='''
            커뮤니티 게시글 신고내역을 생성합니다.<br/>
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
        serializer = self.PostReportCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = PostReportService()

        post_id = data.get('post')
        post = Post.objects.get(id=post_id)

        # request body가 json 방식이 아닌 multipart/form-data 방식으로 전달
        post_report = service.create(
            post=post,
            category=data.get('category'),
            reporter=request.user
        )

        return Response({
            'status': 'success',
            'data': {'id': post_report.id},
        }, status=status.HTTP_201_CREATED)


class PostCommentReportCreateApi(ApiAuthMixin, APIView):
    class PostCommentReportCreateInputSerializer(serializers.Serializer):
        comment = serializers.IntegerField()
        category = serializers.CharField()

        class Meta:
            examples = {
                'comment': 1,
                'category': '게시판 성격에 부적절함'
            }

    @swagger_auto_schema(
        request_body=PostCommentReportCreateInputSerializer,
        security=[],
        operation_id='커뮤니티 댓글 신고내역 생성',
        operation_description='''
            커뮤니티 댓글 신고내역을 생성합니다.<br/>
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
        serializer = self.PostCommentReportCreateInputSerializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = PostCommentReportService()

        comment_id = data.get('comment')
        post_comment = PostComment.objects.get(id=comment_id)

        # request body가 json 방식이 아닌 multipart/form-data 방식으로 전달
        post_comment_report = service.create(
            post_comment=post_comment,
            category=data.get('category'),
            reporter=request.user
        )

        return Response({
            'status': 'success',
            'data': {'id': post_comment_report.id},
        }, status=status.HTTP_201_CREATED)
