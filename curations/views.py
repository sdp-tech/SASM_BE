from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .selectors import CurationSelector, CuratedStoryCoordinatorSelector
from .services import CurationCoordinatorService, CurationLikeService
from .permissions import IsWriter
from curations.models import Curation


class RepCurationListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    class RepCurationListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer = serializers.CharField()
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
                        'writer': 'sdptech@gmail.com',
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
        serializer = self.RepCurationListOutputSerializer(
            curations, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class AdminCurationListApi(APIView):

    class AdminCurationListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer = serializers.CharField()
        is_selected = serializers.BooleanField()

    @swagger_auto_schema(
        operation_id='관리자 큐레이션 리스트',
        operation_description='''
            홈 화면과 모두보기 화면의 관리자 큐레이션을 리스트합니다.<br/>
            관리자 큐레이션이 모두 반환되며, 이 중에서 is_selected=True인 것만 홈 화면에 노출되어야 합니다.<br/>
            Request시 전달해야 할 파라미터는 없습니다.
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '제로웨이스트',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer': 'sdptech@gmail.com',
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
        curations = CurationSelector.admin_curation_list(self)
        serializer = self.AdminCurationListOutputSerializer(
            curations, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class VerifiedUserCurationApi(APIView):

    class VerifiedUserCurationListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer = serializers.CharField()
        is_selected = serializers.BooleanField()

    @swagger_auto_schema(
        operation_id='인증유저 큐레이션 리스트',
        operation_description='''
            홈 화면과 모두보기 화면의 인증유저 큐레이션을 리스트합니다.<br/>
            인증유저 큐레이션이 모두 반환되며, 이 중에서 is_selected=True인 것만 홈 화면에 노출되어야 합니다.<br/>
            Request시 전달해야 할 파라미터는 없습니다.
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '제로웨이스트',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer': 'sdptech@gmail.com',
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
        curations = CurationSelector.verified_user_curation_list(self)
        serializer = self.VerifiedUserCurationListOutputSerializer(
            curations, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class CurationDetailApi(APIView):
    class CruationDetailOutputSerializer(serializers.Serializer):

        title = serializers.CharField()
        contents = serializers.CharField()
        rep_pic = serializers.CharField()
        like_curation = serializers.BooleanField()
        writer = serializers.CharField()
        writer_is_verified = serializers.BooleanField()
        created = serializers.CharField()
        map_image = serializers.CharField()
        # lat, lon

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
                        'writer': 'sdptech@gmail.com',
                        'writer_is_verified': True
                        'map_image': 'https://abc.com/1.jpg',
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
        curation = selector.detail(curation_id=curation_id)
        serializer = self.CruationDetailOutputSerializer(curation, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class CuratedStoryDetailApi(APIView):
    class CuratedStoryDetailOutputSerializer(serializers.Serializer):

        story_id = serializers.IntegerField()
        place_name = serializers.CharField()
        place_address = serializers.CharField()
        place_category = serializers.CharField()
        story_review = serializers.CharField()
        # short_curation = serializers.CharField()
        like_story = serializers.BooleanField()
        hashtags = serializers.CharField()

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
                        'like_story': True,
                        'hashtags': '#버섯농장 #로컬마켓 #성수동 #비건'
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
    class CurationCreateInputSerializer(serializers.Serializer):
        title = serializers.CharField()
        contents = serializers.CharField()
        stories = serializers.ListField()
        short_curations = serializers.ListField()
        rep_pic = serializers.ImageField()
        # is_released
        # is_selected
        # is_rep

        class Meta:
            examples = {
                'title': '서울 제로웨이스트샵 5곳',
                'contents': '서울에서 제로웨이스트샵을 만나보세요.',
                'stories': ['1', '2', '3'],
                'short_curations': ['스토리1에 대한 숏큐입니다.', '스토리2에 대한 숏큐입니다.', '스토리3에 대한 숏큐입니다.'],
                'rep_pic': 'https://abc.com/1.jpg'
            }

    @swagger_auto_schema(
        request_body=CurationCreateInputSerializer,
        security=[],
        operation_id='큐레이션 생성',
        operation_description='''
            큐레이션을 생성합니다.<br/>
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
            rep_pic=data.get('rep_pic')
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
        rep_pic = serializers.ImageField()

        class Meta:
            examples = {
                'title': '서울 제로웨이스트샵 5곳',
                'content': '서울에서 제로웨이스트샵을 만나보세요.',
                'stories': ['1', '2', '3'],
                'short_curations': ['스토리1에 대한 숏큐입니다.', '스토리2에 대한 숏큐입니다.', '스토리3에 대한 숏큐입니다.'],
                'photo_image_url': 'https://abc.com/1.jpg',
                'rep_pic': 'https://abc.com/2.jpg'
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

    class CurationLikeInputSerializer(serializers.Serializer):
        curation = serializers.IntegerField()

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
    def post(self, request):
        serializer = self.CurationLikeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        curation = get_object_or_404(
            Curation, id=data.get('curation'))
        likes = CurationLikeService.like_or_dislike(
            curation=curation,
            user=request.user
        )

        return Response({
            'status': 'success',
            'data': {'likes': likes},
        }, status=status.HTTP_200_OK)
