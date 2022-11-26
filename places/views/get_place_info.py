from django.db.models import Q
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema

from places.models import Place
from places.serializers import PlaceSerializer,PlaceDetailSerializer, MapMarkerSerializer
from sasmproject.swagger import param_search,param_filter,param_id

class MapMarkerView(viewsets.ModelViewSet):
    '''
        map marker 표시를 위해 모든 장소를 주는 API
    '''
    queryset = Place.objects.all().values('place_name', 'latitude', 'longitude', 'id')
    serializer_class = MapMarkerSerializer
    permission_classes=[
        AllowAny,
    ]
    @swagger_auto_schema(operation_id='api_places_map_info_get',security=[])
    def get(self, request):
        serializer = MapMarkerSerializer(self.queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
class BasicPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

class PlaceListView(viewsets.ModelViewSet):
    '''
        place의 list의 정보를 주는 API
    '''
    queryset = Place.objects.prefetch_related('place_likeuser_set').values()
    serializer_class = PlaceSerializer
    permission_classes=[
        AllowAny,
    ]
    pagination_class=BasicPagination

    def filter_if_given(array):
        query = None
        for a in array: 
            if query is None: 
                query = Q(category=a) 
            else: 
                query = query | Q(category=a)
        return query

    def search_if_given(self,search):
        if(search):
            qs = self.get_queryset().filter(Q(place_name__icontains=search))
            return qs
        else:
            qs = self.get_queryset()
        return qs

    @swagger_auto_schema(operation_id='api_places_place_search_get',
                        manual_parameters=[param_search,param_filter],security=[])
    def get(self, request):
        '''
        search,filter를 적용한 장소 리스트를 distance로 정렬하여 반환
        '''
        search = request.GET.get('search','')
        qs = self.search_if_given(search)
        array = request.query_params.getlist('filter[]', '배열')
        if array != '배열':
            query = self.filter_if_given(array)
            qs = qs.filter(query)
        serializer = self.get_serializer(
            qs,
            many=True,
            context={
                "left":request.query_params.get("left"),
                "right":request.query_params.get("right"),
                "request":request
            }
        )
        
        # 검색 결과를 바탕으로 거리순 정렬 후 pagination
        serializer_data = sorted(
            serializer.data, key=lambda k: float(k['distance']))
        page = self.paginate_queryset(serializer_data)
    
        if page is not None:
            serializer = self.get_paginated_response(page)
        else:
            serializer = self.get_serializer(page, many=True)
            
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
class PlaceDetailView(viewsets.ModelViewSet):
    '''
        place의 detail 정보를 주는 API
    '''
    queryset = Place.objects.select_related('story')
    serializer_class = PlaceDetailSerializer
    permission_classes=[
        AllowAny,
    ]
    @swagger_auto_schema(operation_id='api_places_place_detail_get',
                        manual_parameters=[param_id],security=[])
    def get(self,request):
        '''
            Place의 detail한 정보를 주는 api
        '''
        pk = request.GET.get('id', '')
        place = self.get_queryset().get(id=pk)
        return Response({
            'status': 'success',
            'data': PlaceDetailSerializer(place,context={'request': request}).data,
        }, status=status.HTTP_200_OK)
