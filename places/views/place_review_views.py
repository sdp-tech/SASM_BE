from rest_framework import status
from rest_framework import viewsets
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from places.models import PlaceVisitorReview, Place
from places.mixins import ApiAuthMixin
from places.serializers import VisitorReviewSerializer
from places.services import PlaceVisitorReviewCoordinatorService, PlaceVisitorReviewService
from places.selectors import PlaceVisitorReviewCoordinatorSelector, PlaceReviewSelector
from sasmproject.swagger import param_pk, param_id


class BasicPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'


class PlaceVisitorReviewCreateApi(APIView, ApiAuthMixin):
    class PlaceVisitorReviewSerializer(serializers.Serializer):
        place = serializers.CharField()
        contents = serializers.CharField()
        category = serializers.CharField(required=False)
        photos = serializers.ListField(required=False)

    @swagger_auto_schema(
        operation_id='',
        operation_description='''
            장소 리뷰를 생성하는 api
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
            )
        }
    )
    def post(self, request):
        serializer = self.PlaceVisitorReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = PlaceVisitorReviewCoordinatorService(
            user=request.user
        )

        place_review = service.create(
            place_id=data.get('place'),
            contents=data.get('contents'),
            images=data.get('photos', []),
            category=data.get('category', '')
        )

        return Response({
            'status': 'success',
            'data': {'id': place_review.id},
        }, status=status.HTTP_200_OK)


class PlaceVisitorReviewUpdateApi(APIView, ApiAuthMixin):
    class PlaceVisitorReviewSerializer(serializers.Serializer):
        place = serializers.CharField()
        contents = serializers.CharField()
        category = serializers.CharField(required=False)
        photoList = serializers.ListField(required=False)
        photos = serializers.ListField(required=False)

        class Meta:
            examples = {
                'place': '안녕 상점 추천합니다.',
                'contents': '개인적으로 좋았습니다.',
                'category': '1,2,5',
                'photoList': ['https://abc.com/2.jpg'],
                'photos': ['<IMAGE FILE BINARY>', '<IMAGE FILE BINARY>'],
            }

    @swagger_auto_schema(
        request_body=PlaceVisitorReviewSerializer,
        security=[],
        operation_id='장소 리뷰 업데이트',
        operation_description='''
            전송된 모든 필드 값을 그대로 댓글에 업데이트하므로, 댓글에 포함되어야 하는 모든 필드 값이 request body에 포함되어야합니다.<br/>
            즉, 값이 수정된 필드뿐만 아니라 값이 그대로 유지되어야하는 필드도 함께 전송되어야합니다.<br/>
            <br/>
            photoList 사용 예시로, 게시글 디테일 API에서 전달받은 photoList 값이 ['https://abc.com/1.jpg', 'https://abc.com/2.jpg']일 때 '1.jpg'를 지우고 싶다면 ['https://abc.com/2.jpg']으로 값을 설정하면 됩니다.<br/>
            만약 새로운 photo를 추가하고 싶다면, photos에 이미지 첨부 파일을 1개 이상 담아 전송하면 됩니다.<br/>
            <br/>
            참고로 request body는 json 형식이 아닌 <b>multipart/form-data 형식</b>으로 전달받으므로, 리스트 값을 전달하고자 한다면 개별 원소들마다 리스트 필드 이름을 key로 설정하여, 원소 값을 value로 추가해주면 됩니다.
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
            )
        }
    )
    def put(self, request, place_review_id):
        serializer = self.PlaceVisitorReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = PlaceVisitorReviewCoordinatorService(
            user=request.user
        )

        service.update(
            place_review_id=place_review_id,
            contents=data.get('contents'),
            category=data.get('category', ''),
            photo_image_urls=data.get('photoList', []),
            image_files=data.get('photos', []),
        )

        return Response({
            'status': 'success',
            'data': {'id': place_review_id},
        }, status=status.HTTP_200_OK)


def get_paginated_response(*, pagination_class, serializer_class, queryset, request, view):
    paginator = pagination_class()

    page = paginator.paginate_queryset(queryset, request, view=view)

    if page is not None:
        serializer = serializer_class(page, many=True)
    else:
        serializer = serializer_class(queryset, many=True)

    # get category statistics
    selector = PlaceReviewSelector()
    category_statistics = selector.get_category_statistics(
        place_id=request.GET['place_id'])

    data = paginator.get_paginated_response(serializer.data).data
    data['statistics'] = category_statistics
    # data.results 앞에 위치하도록 OrderedDict 내 순서 조정
    data.move_to_end('statistics', last=False)

    return Response({
        'status': 'success',
        'data': data,
    }, status=status.HTTP_200_OK)


class PlaceVisitorReviewListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 5
        page_size_query_param = 'page_size'

    class PlaceVisitorReviewListInputSerializer(serializers.Serializer):
        place_id = serializers.IntegerField()

    class PlaceVisitorReviewListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        # place = serializers.IntegerField()
        contents = serializers.CharField()
        created = serializers.CharField()
        updated = serializers.CharField()

        nickname = serializers.CharField()
        photoList = serializers.ListField(required=False)
        categoryList = serializers.ListField(required=False)

        class Meta:
            model = PlaceVisitorReview
            fields = [
                'id',
                'contents',
                'created',
                'updated',
            ]

    @swagger_auto_schema(
        query_serializer=PlaceVisitorReviewListInputSerializer,
        security=[],
        operation_id='장소 리뷰 리스트 조회',
        operation_description='''
            장소 리뷰 리스트를 반환합니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                            "status": "success",
                        "data": {
                            "statistics": [
                                ["분위기가 좋다", 33],
                                ["전시가 멋지다", 27],
                                ["청결하다", 17]
                            ],
                            "count": 3,
                            "next": 1,
                            "previous": 2,
                            "results": [
                                {
                                    "id": 91,
                                    "contents": "좋다, 멋지다",
                                    "created": "2023-03-20 06:31:51.241182+00:00",
                                    "updated": "2023-03-20 10:41:57.988675+00:00",
                                    "nickname": "닉넴",
                                    "photoList": [
                                                {
                                                    "imgfile": "https://sasm-bucket.s3.amazonaws.com/media/ABC.jpeg"
                                                },
                                        {
                                                    "imgfile": "https://sasm-bucket.s3.amazonaws.com/media/123.png"
                                                }
                                    ],
                                    "categoryList": ["1", "11"]
                                }
                            ]
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        input_serializer = self.PlaceVisitorReviewListInputSerializer(
            data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        place_filter = input_serializer.validated_data

        selector = PlaceVisitorReviewCoordinatorSelector()
        reviews = selector.list(
            place_id=place_filter.get('place_id')
        )

        paginated_response = get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.PlaceVisitorReviewListOutputSerializer,
            queryset=reviews,
            request=request,
            view=self
        )

        return paginated_response


class PlaceReviewView(viewsets.ModelViewSet):
    queryset = PlaceVisitorReview.objects.select_related(
        'visitor_name').order_by('-created')
    serializer_class = VisitorReviewSerializer
    pagination_class = BasicPagination

    def get_permissions(self):
        """
        함수에 따른 permissions customize
        """
        if self.action == 'save_review' or self.action == 'put':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(operation_id='api_places_save_review_post')
    @action(detail=False, methods=['post'])
    def save_review(self, request):
        '''
        장소 리뷰를 저장하는 api
        '''
        review_info = request.data
        serializer = VisitorReviewSerializer(
            data=review_info, context={'request': request})

        try:
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "data": serializer.data,
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "fail",
                    "data": serializer.errors
                })

        except:
            return Response({
                "status": "fail",
                "data": serializer.errors,
                "message": "can upload upto three"
            })

    @swagger_auto_schema(operation_id='api_places_place_review_retreive_get', manual_parameters=[param_pk])
    def retrieve(self, request, *args, **kwargs):
        '''
        장소 리뷰를 보여주는 api
        '''
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'status': 'Success',
            'data': response.data,
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_places_place_review_list_get', manual_parameters=[param_id])
    def list(self, request):
        '''
        장소에 대한 review list를 반환하는 api
        '''
        pk = request.GET.get('id', '')
        queryset = PlaceVisitorReview.objects.filter(place_id=pk)
        serializer = self.get_serializer(
            queryset, many=True, context={'request': request})
        page = self.paginate_queryset(serializer.data)
        if page is not None:
            serializer = self.get_paginated_response(page)
        else:
            serializer = self.get_serializer(page, many=True)
        return Response({
            'status': 'Success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_places_place_review_put', manual_parameters=[param_pk])
    def put(self, request, pk):
        '''
        장소 리뷰 수정하는 api
        '''
        board = self.get_object()
        serializer = VisitorReviewSerializer(board, data=request.data, context={
                                             'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)
        return Response({
            "status": "fail",
            "data": serializer.errors,
        })
