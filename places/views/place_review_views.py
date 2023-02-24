from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from places.models import VisitorReview
from places.serializers import VisitorReviewSerializer
from places.services import PlaceReviewCoordinatorService
from places.selectors import PlaceReviewCoordinatorSelector
from sasmproject.swagger import param_pk,param_id

from rest_framework.views import APIView
from community.mixins import ApiAuthMixin
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class BasicPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'


class PlaceReviewListApi(APIView, ApiAuthMixin):
    class PlaceReviewOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        nickname = serializers.CharField()
        place = serializers.IntegerField()
        contents = serializers.CharField()
        photos = serializers.ListField(required=False)
        category = serializers.ListField(required=False)
        created = serializers.CharField()
        updated = serializers.CharField()
        writer = serializers.CharField()


    @swagger_auto_schema(
        operation_id='',
        operation_description='''
            장소 리뷰를 보여주는 api
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples = {
                "id": 1,
                "nickname": "스드프",
                "place": 1,
                "contents": "기다린 보람이 있네요",
                "photos": [
                    {
                        "imgfile": "https://sasm-bucket/123.png"
                    },
                    {
                        "imgfile": "https://sasm-bucket/456.png"
                    }
                ],
                "category": [
                    {
                        "category": 1
                    },
                    {
                        "category": 7
                    }
                ],
                "created": "2023-02-23T21:16:33.454291+09:00",
                "updated": "2023-02-23T21:16:33.454330+09:00",
                "writer": "sdp@sdp.com"
            }
            ),
            "400": openapi.Response(
                description="Bad Request",
            )
        }
    )
    def get(self, request):
        selector = PlaceReviewCoordinatorSelector
        place_list = selector.list(
            place_id = request.query_params.get('id')
        )
        
        serializer = self.PlaceReviewOutputSerializer(place_list, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class PlaceReviewCreateApi(APIView, ApiAuthMixin):
    class PlaceReviewInputSerializer(serializers.Serializer):
        place = serializers.CharField() # form-data
        contents = serializers.CharField()
        category = serializers.CharField() 
        photos = serializers.ImageField()

    class PlaceReviewOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        nickname = serializers.CharField()
        place = serializers.IntegerField()
        contents = serializers.CharField()
        photos = serializers.ListField(required=False)
        category = serializers.ListField(required=False)
        created = serializers.CharField()
        updated = serializers.CharField()
        writer = serializers.CharField()


    @swagger_auto_schema(
        operation_id='',
        operation_description='''
            장소 리뷰를 보여주는 api
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples = {
                "id": 1,
                "nickname": "스드프",
                "place": 1,
                "contents": "기다린 보람이 있네요",
                "photos": [
                    {
                        "imgfile": "https://sasm-bucket/123.png"
                    },
                    {
                        "imgfile": "https://sasm-bucket/456.png"
                    }
                ],
                "category": [
                    {
                        "category": 1
                    },
                    {
                        "category": 7
                    }
                ],
                "created": "2023-02-23T21:16:33.454291+09:00",
                "updated": "2023-02-23T21:16:33.454330+09:00",
                "writer": "sdp@sdp.com"
            }
            ),
            "400": openapi.Response(
                description="Bad Request",
            )
        }
    )

    def list(self, request):        
        serializer = self.PlaceReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = PlaceReviewCoordinatorService(
            user = request.user
        )
        
        post_review = service.create(
            place = data.get('place'),
            contents = data.get('contents'),
            photos = data.get('photos', []),
            category = data.get('category', [])
        )

        selector = PlaceReviewCoordinatorSelector
        post_review_qs = selector.get_created(
            place_id = post_review.id
        )

        serializer = self.PlaceReviewOutputSerializer(post_review_qs, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class PlaceReviewView(viewsets.ModelViewSet):
    queryset = VisitorReview.objects.select_related('visitor_name').order_by('-created')
    serializer_class = VisitorReviewSerializer
    pagination_class=BasicPagination

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
        serializer = self.get_serializer(data=review_info, context={'request': request})
        serializer.is_valid()  

        try:
            if serializer.is_valid():
                serializer.save()
                return Response({
                        "status" : "success",
                        "data" : serializer.data,
                    },status=status.HTTP_200_OK)
            else:
                return Response({
                    "status" : "fail",
                    "data" : serializer.errors
                })        
                    
        except:
            return Response({
                "status" : "fail",
                "data" : serializer.errors,
                "message" : "can upload upto three"
            })

    @swagger_auto_schema(operation_id='api_places_place_review_retreive_get',manual_parameters=[param_pk])
    def retrieve(self, request, *args, **kwargs):
        '''
        장소 리뷰를 보여주는 api
        '''
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'status': 'Success',
            'data': response.data,
            },status=status.HTTP_200_OK)
    
    @swagger_auto_schema(operation_id='api_places_place_review_list_get',manual_parameters=[param_id])
    def list(self, request):
        '''
        장소에 대한 review list를 반환하는 api
        '''
        pk = request.GET.get('id','')
        queryset = VisitorReview.objects.filter(place_id=pk)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        page = self.paginate_queryset(serializer.data)
        if page is not None:
            serializer = self.get_paginated_response(page)
        else:
            serializer = self.get_serializer(page, many=True)
        return Response({
            'status': 'Success',
            'data': serializer.data,
            },status=status.HTTP_200_OK)
    
    @swagger_auto_schema(operation_id='api_places_place_review_put',manual_parameters=[param_pk])
    def put(self, request, pk):
        '''
        장소 리뷰 수정하는 api
        '''
        board = self.get_object()
        serializer  = VisitorReviewSerializer(board, data=request.data, context={'request': request}, partial=True)
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