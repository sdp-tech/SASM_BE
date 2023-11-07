from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, AllowAny


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .selectors import CurationSelector, CuratedStoryCoordinatorSelector, TotalSearchSelector
from .services import CurationCoordinatorService, CurationLikeService
from .permissions import IsWriter, IsVerifiedOrSdpAdmin
from curations.models import Curation


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


class CurationListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 8
        page_size_query_param = 'page_size'

    class CurationListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        order = serializers.CharField(required=False)

    class CurationListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer_email = serializers.CharField()
        nickname = serializers.CharField()
        is_selected = serializers.BooleanField()

    @swagger_auto_schema(
        query_serializer=CurationListFilterSerializer,
        operation_id='큐레이션 검색 결과 리스트',
        operation_description='''
            큐레이션의 검색 결과를 리스트합니다.<br/>
            search(검색어)의 default값은 ''로, 검색어가 없을 시 모든 큐레이션이 반환됩니다.
            order(정렬)은 latest 또는 oldest로 최신순 정렬 여부를 결정합니다.
            반환되는 정보는 대표/관리자/인증유저 큐레이션 <b>모두보기 레이아웃</b>에서 볼 수 있는 것과 같습니다.
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '서울 비건카페 탑5',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_email': 'sdptech@gmail.com',
                        'nickname':'sdpygl',
                        'is_selected': True,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.CurationListFilterSerializer(
            data=request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        curations = CurationSelector.list(
            search=filters.get('search', ''),
            order = filters.get('order', '')
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.CurationListOutputSerializer,
            queryset=curations,
            request=request,
            view=self
        )


class RepCurationListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class RepCurationListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer_email = serializers.CharField()
        is_selected = serializers.BooleanField()

    @swagger_auto_schema(
        operation_id='대표큐레이션 리스트',
        operation_description='''
            홈 화면과 모두보기 화면의 대표큐레이션을 리스트합니다.<br/>
            대표큐레이션이 모두 반환되며, 이 중에서 is_selected=True인 것만 홈 화면에 노출되어야 합니다.<br/>
            Request시 전달해야 할 파라미터는 없습니다.
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '서울 비건카페 탑5',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_email': 'sdptech@gmail.com',
                        'is_selected': True,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        curations = CurationSelector.rep_curation_list(self)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.RepCurationListOutputSerializer,
            queryset=curations,
            request=request,
            view=self
        )


class AdminCurationListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class AdminCurationListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)

    class AdminCurationListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer_email = serializers.CharField()
        nickname=serializers.CharField()
        is_selected = serializers.BooleanField()

    @swagger_auto_schema(
        operation_id='관리자 큐레이션 리스트',
        operation_description='''
            홈 화면과 모두보기 화면의 관리자 큐레이션을 리스트합니다.<br/>
            search(검색어)의 default값은 ''로, 검색어가 없을 시 모든 관리자 큐레이션이 반환됩니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '제로웨이스트',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_email': 'sdptech@gmail.com',
                        'nickname':'sdpygl',
                        'is_selected': True,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.AdminCurationListFilterSerializer(
            data=request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        curations = CurationSelector.admin_curation_list(
            search=filters.get('search', '')
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.AdminCurationListOutputSerializer,
            queryset=curations,
            request=request,
            view=self
        )


class VerifiedUserCurationListApi(APIView):
    permission_classes = (AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class VerifiedUserCurationListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer_email = serializers.CharField()
        nickname=serializers.CharField()
        is_selected = serializers.BooleanField()

    class VerifiedUserCurationListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)

    @swagger_auto_schema(
        operation_id='인증유저 큐레이션 리스트',
        operation_description='''
            홈 화면과 모두보기 화면의 인증유저 큐레이션을 리스트합니다.<br/>
            search(검색어)의 default값은 ''로, 검색어가 없을 시 모든 인증유저 큐레이션이 반환됩니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '제로웨이스트',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_email': 'sdptech@gmail.com',
                        'nickname':'sdpygl',
                        'is_selected': True,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.VerifiedUserCurationListFilterSerializer(
            data=request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        curations = CurationSelector.verified_user_curation_list(
            search=filters.get('search', '')
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.VerifiedUserCurationListOutputSerializer,
            queryset=curations,
            request=request,
            view=self
        )


class CurationDetailApi(APIView):
    permission_classes = (AllowAny, )

    class CurationDetailOutputSerializer(serializers.Serializer):
        title = serializers.CharField()
        contents = serializers.CharField()
        rep_pic = serializers.CharField()
        like_curation = serializers.BooleanField()
        writer_email = serializers.CharField()
        nickname = serializers.CharField()
        profile_image = serializers.CharField()
        writer_is_verified = serializers.BooleanField()
        created = serializers.CharField()
        updated = serializers.CharField()
        map_image = serializers.CharField()
        writer_is_followed = serializers.BooleanField()
        like_cnt = serializers.IntegerField()

    @swagger_auto_schema(
        operation_id='큐레이션 디테일 조회',
        operation_description='''
            큐레이션 디테일을 조회합니다.<br/>
            큐레이션 상세페이지 상단에 해당하는, 스토리를 제외한 큐레이션의 기본 정보를 반환합니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'title': '서울 비건카페',
                        'contents': '서울 비건카페 5곳을 소개합니다',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'like_curation': True,
                        'writer_email': 'sdptech@gmail.com',
                        'nickname': '스드프',
                        'profile_image': 'https://abc.com/1.jpg',
                        'writer_is_verified': True,
                        'created' : "2023-08-20 10:59:09.765298+00:00",
                        "updated": "2023-08-20 11:40:18.412855+00:00",
                        'map_image': 'https://abc.com/1.jpg',
                        'writer_is_followed': True,
                        'liked_cnt' : 0,
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request, curation_id):
        selector = CurationSelector(user=request.user)
        curation = selector.detail(curation_id=curation_id, user=request.user)
        serializer = self.CurationDetailOutputSerializer(curation)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class CuratedStoryDetailApi(APIView):
    permission_classes = (AllowAny, )

    class CuratedStoryDetailOutputSerializer(serializers.Serializer):

        story_id = serializers.IntegerField()
        place_name = serializers.CharField()
        place_address = serializers.CharField()
        place_category = serializers.CharField()
        story_review = serializers.CharField()
        preview = serializers.CharField()
        # short_curation = serializers.CharField()
        like_story = serializers.BooleanField()
        hashtags = serializers.CharField()
        rep_photos = serializers.ListField(required=False)
        rep_pic = serializers.CharField()

        writer_email = serializers.CharField()
        nickname = serializers.CharField()
        profile_image = serializers.CharField()
        created = serializers.CharField()
        writer_is_followed = serializers.BooleanField()

    @swagger_auto_schema(
        operation_id='큐레이션 스토리 디테일 조회',
        operation_description='''
            큐레이션 내 스토리 정보를 반환합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'story_id': 1,
                        'place_name': '르타리',
                        'place_address': '연세로',
                        'place_category': '식당 및 카페',
                        'place_review': '버섯에서 발견한 도시의 지속가능성',
                        'preview': '성수동에서 찾은 지속가능성의 의미',
                        'like_story': True,
                        'hashtags': '#버섯농장 #로컬마켓 #성수동 #비건',
                        'rep_photos':  "['https://abc.com/1.jpg', 'https://abc.com/2.jpg', 'https://abc.com/3.jpg']",
                        'writer_email': 'sdp.tech@gmail.com',
                        'nickname': '스드프',
                        'profile_image': 'https://abc.com/1.jpg',
                        'created': '2022-08-24T14:15:22Z',
                        'rep_pic': 'https://sasm-bucket.s3.amazonaws.com/media/stories/img/pic01.jpg',
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request, curation_id):
        selector = CuratedStoryCoordinatorSelector(user=request.user)
        curation = selector.detail(curation_id=curation_id)
        serializer = self.CuratedStoryDetailOutputSerializer(
            curation, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class CurationCreateApi(APIView):
    permission_classes = (IsVerifiedOrSdpAdmin, )

    class CurationCreateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        contents = serializers.CharField()
        stories = serializers.ListField()
        short_curations = serializers.ListField()
        rep_pic = serializers.ImageField()
        is_released = serializers.BooleanField(
            required=False, default=True)  # 개발용
        is_selected = serializers.BooleanField(
            required=False, default=True)  # 개발용
        is_rep = serializers.BooleanField(required=False, default=True)  # 개발용

        class Meta:
            examples = {
                'title': '서울 제로웨이스트샵 5곳',
                'contents': '서울에서 제로웨이스트샵을 만나보세요.',
                'stories': ['1', '2', '3'],
                'short_curations': ['스토리1에 대한 숏큐입니다.', '스토리2에 대한 숏큐입니다.', '스토리3에 대한 숏큐입니다.'],
                'rep_pic': '<IMAGE FILE BINARY>',
            }

    @swagger_auto_schema(
        request_body=CurationCreateInputSerializer,
        security=[],
        operation_id='큐레이션 생성',
        operation_description='''
            큐레이션을 생성합니다.<br/>
            short_curations 리스트 요소 순서는 해당하는 stories 순서와 일치해야 합니다.<br/>
            현재 큐레이션을 생성하면 <b>대표큐레이션이자, 홈 화면 노출 대상으로 자동 설정됩니다.</b>
            큐레이션 작성자가 인증된 유저이면 해당 큐레이션은 인증유저큐레이션이자 대표큐레이션이며,
            마찬가지로 작성자가 관리자이면 해당 큐레이션은 관리자큐레이션이자 대표큐레이션이 됩니다.<br/>
            Request example에는 명시하지 않았으나 관련 부분 테스트가 필요하다면
            'is_rep' : False (대표큐레이션 설정 취소), 'is_selected' : False (홈 화면 노출 취소) 형태로 전달하면 됩니다. 
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "id": 1
                        }
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
        serializer = self.CurationCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = CurationCoordinatorService(user=request.user)

        curation = service.create(
            title=data.get('title'),
            contents=data.get('contents'),
            stories=data.get('stories'),
            short_curations=data.get('short_curations'),
            rep_pic=data.get('rep_pic'),
            is_released=data.get('is_released'),  # 개발용
            is_selected=data.get('is_selected'),  # 개발용
            is_rep=data.get('is_rep')  # 개발용
        )

        return Response({
            'status': 'success',
            'data': {'id': curation.id},
        }, status=status.HTTP_200_OK)


class CurationUpdateApi(APIView):
    permission_classes = (IsWriter, )

    def get_object(self, curation_id):
        curation = get_object_or_404(Curation, pk=curation_id)
        self.check_object_permissions(self.request, curation)
        return curation

    class CurationUpdateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        contents = serializers.CharField()
        stories = serializers.ListField()
        short_curations = serializers.ListField()
        photo_image_url = serializers.CharField()
        rep_pic = serializers.ImageField(default=None)

        class Meta:
            examples = {
                'title': '서울 제로웨이스트샵 5곳',
                'content': '서울에서 제로웨이스트샵을 만나보세요.',
                'stories': ['1', '2', '3'],
                'short_curations': ['스토리1에 대한 숏큐입니다.', '스토리2에 대한 숏큐입니다.', '스토리3에 대한 숏큐입니다.'],
                'photo_image_url': 'https://abc.com/1.jpg',
                'rep_pic': '<IMAGE FILE BINARY>'
            }

    @swagger_auto_schema(
        request_body=CurationUpdateInputSerializer,
        security=[],
        operation_id='큐레이션 수정',
        operation_description='''
            큐레이션을 수정합니다.<br/>
            값이 수정된 필드뿐만 아니라 값이 그대로 유지되어야하는 필드도 함께 전송되어야 합니다.<br/>
            short_curations 리스트 요소 순서는 해당하는 stories 순서와 일치해야 합니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {
                            "id": 1
                        }
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def put(self, request, curation_id):
        curation = self.get_object(curation_id)

        serializers = self.CurationUpdateInputSerializer(
            data=request.data)
        serializers.is_valid(raise_exception=True)
        data = serializers.validated_data

        service = CurationCoordinatorService(
            user=request.user
        )

        curation = service.update(
            title=data.get('title'),
            curation=curation,
            contents=data.get('contents'),
            stories=data.get('stories'),
            short_curations=data.get('short_curations'),
            photo_image_url=data.get('photo_image_url', ''),
            rep_pic=data.get('rep_pic'),
        )

        return Response({
            'status': 'success',
            'data': {'id': curation.id},
        }, status=status.HTTP_200_OK)


class CurationDeleteApi(APIView):
    permission_classes = (IsWriter, )

    def get_object(self, curation_id):
        curation = get_object_or_404(Curation, pk=curation_id)
        self.check_object_permissions(self.request, curation)
        return curation

    @swagger_auto_schema(
        operation_id='큐레이션 삭제',
        operation_description='''
            전달된 id를 가지는 큐레이션을 삭제합니다.<br/>
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
    def delete(self, request, curation_id):
        curation = self.get_object(curation_id)

        service = CurationCoordinatorService(
            user=request.user
        )

        service.delete(
            curation=curation
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class CurationLikeApi(APIView):
    permission_classes = (IsAuthenticated, )

    def get_object(self, curation_id):
        curation = get_object_or_404(Curation, pk=curation_id)
        self.check_object_permissions(self.request, curation)
        return curation

    @swagger_auto_schema(
        operation_id='큐레이션 좋아요/좋아요 취소',
        operation_description='''
            해당 큐레이션에 대해 좋아요/좋아요 취소를 수행합니다.<br/>
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
    def post(self, request, curation_id):
        curation = get_object_or_404(
            Curation, pk=curation_id)
        likes = CurationLikeService.like_or_dislike(
            curation=curation,
            user=request.user
        )

        return Response({
            'status': 'success',
            'data': {'likes': likes},
        }, status=status.HTTP_200_OK)
    
class TotalSearchApi(APIView):
    permission_classes=(AllowAny, )

    class Pagination(PageNumberPagination):
        page_size = 8
        page_size_query_param = 'page_size'

    class TotalSearchFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        order = serializers.CharField(required=False)

    class TotalSearchOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        model = serializers.CharField()
        title = serializers.CharField()
        #content는 curation에서는 content를, forest에서는 subtitle을, story에서는 preview를 의미한다.
        content = serializers.CharField()
        #like_cnt는 curation, forest의 like_cnt를, place의 place_like_cnt, story의 story_like_cnt를 의미
        like_cnt = serializers.IntegerField()
        writer_is_followed = serializers.BooleanField()
        created = serializers.CharField()
        rep_pic = serializers.CharField()
        nickname = serializers.CharField()
        user_likes=serializers.BooleanField()

    @swagger_auto_schema(
        query_serializer=TotalSearchFilterSerializer,
        operation_id='통합 검색 결과 리스트',
        operation_description='''
            통합 검색 결과를 리스트합니다.</br>
            search(검색어)의 default값은 ''로, 검색어가 없을 시 아무것도 반환되지 않습니다.
            order(정렬)은 latest 또는 oldest로 최신순 정렬 여루블 결정합니다.
            반환되는 정보는</br>
            1. id </br>
            2. model(ex. Curation, Forest, Story) </br>
            3. title </br>
            4. content (curation: content, forest: subtitle, story: preview) </br>
            5. 좋아요 수 like_cnt(curation, forest: like_cnt, story: story_like_cnt) </br>
            6. 작성자 팔로우 여부 writer_is_followed </br>
            7. 생성일자 created </br>
            8. 대표사진 rep_pic </br>
            9. 작성자 nickname </br>
            10. 유저 좋아요 여부 user_likes

            ''',
        response={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json":{
                        'id':1,
                        'model': 'Curation',
                        'title': '서울 비건카페',
                        'content': '서울 비건카페 5곳을 소개합니다',
                        'like_cnt': 0,
                        'writer_is_followed': True,
                        'created': "2023-08-20 10:59:09.765298+00:00",
                        'rep_pic': 'https://abc.com/1.jpg',
                        'nickname': '스드프',
                        'user_likes': True,
                    }
                }
            ),
            "400":openapi.Response(
                description="Bad Request",
            ),
        }
    )

    def get(self,request):
        filters_serializer = self.TotalSearchFilterSerializer(
            data = request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        results = TotalSearchSelector.list(
            search=filters.get('search', ''),
            order = filters.get('order', ''),
            user=request.user
        )
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.TotalSearchOutputSerializer,
            queryset=results,
            request=request,
            view=self
        )