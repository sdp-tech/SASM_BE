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

from places.models import PlaceVisitorReview
from places.mixins import ApiAuthMixin
from places.serializers import VisitorReviewSerializer
from places.services import PlaceVisitorReviewCoordinatorService, PlaceVisitorReviewService
from sasmproject.swagger import param_pk,param_id

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
            user = request.user
        )

        place_review = service.create(
            place_id = data.get('place'),
            contents = data.get('contents'),
            photos = data.get('photos', []),
            category = data.get('category', '')
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
        photos = serializers.ListField(required=False)

    @swagger_auto_schema(
        operation_id='',
        operation_description='''
            장소 리뷰를 수정하는 api
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
        serializer  = self.PlaceVisitorReviewSerializer(data=request.data)
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


class PlaceReviewView(viewsets.ModelViewSet):
    queryset = PlaceVisitorReview.objects.select_related('visitor_name').order_by('-created')
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
        queryset = PlaceVisitorReview.objects.filter(place_id=pk)
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