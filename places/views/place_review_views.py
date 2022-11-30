from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from places.models import VisitorReview
from places.serializers import VisitorReviewSerializer
from sasmproject.swagger import param_pk,param_id
class BasicPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'

class PlaceReviewView(viewsets.ModelViewSet):
    queryset = VisitorReview.objects.select_related('visitor_name').order_by('-created')
    serializer_class = VisitorReviewSerializer
    permission_classes = [
        IsAuthenticated
    ]
    pagination_class=BasicPagination

    @swagger_auto_schema(operation_id='api_places_save_review_post')
    @action(detail=False, methods=['post'])
    def save_review(self, request):
        '''
        장소 리뷰를 저장하는 api
        '''
        review_info = request.data
        serializer = VisitorReviewSerializer(data=review_info, context={'request': request})
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
        장소 list를 반환하는 api
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
