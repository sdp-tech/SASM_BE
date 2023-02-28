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

from places.models import VisitorReview
from places.mixins import ApiAuthMixin
from places.serializers import VisitorReviewSerializer
from places.services import PlaceReviewCoordinatorService, PlaceReviewService
from places.selectors import PlaceReviewCoordinatorSelector
from sasmproject.swagger import param_pk,param_id

class BasicPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'

class PlaceReviewCreateApi(APIView, ApiAuthMixin):
    class PlaceReviewInputSerializer(serializers.Serializer):
        place = serializers.CharField()
        contents = serializers.CharField()
        category = serializers.CharField(required=False) 
        photos = serializers.ImageField(required=False)

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
            장소 리뷰를 생성하는 api
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

    def post(self, request):        
        serializer = self.PlaceReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = PlaceReviewCoordinatorService(
            user = request.user
        )

        place_review = service.create(
            place = data.get('place'),
            contents = data.get('contents'),
            photos = data.get('photos', None),
            category = data.get('category', None)
        )

        selector = PlaceReviewCoordinatorSelector
        place_review_qs = selector.get_instance(
            place_review_id = place_review.id
        )

        serializer = self.PlaceReviewOutputSerializer(place_review_qs, many=True)

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
        serializer = VisitorReviewSerializer(data=review_info, context={'request': request})
        
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