from django.db.models import Q
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError
from rest_framework import serializers

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from places.mixins import ApiAuthMixin
from places.models import Place
from places.serializers import PlaceSerializer, PlaceDetailSerializer
from places.selectors import PlaceSelector
from sasmproject.swagger import param_search, param_filter, param_id


class MapMarkerApi(APIView, ApiAuthMixin):
    class MapMarkerOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        place_name = serializers.CharField()
        longitude = serializers.FloatField(required=False)
        latitude = serializers.FloatField(required=False)

    @swagger_auto_schema(
        operation_id='',
        operation_description='''
            map marker 표시를 위해 모든 장소를 주는 API
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '비건마마',
                        'longitude': '45.2',
                        'latitue': '15.0',
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            )
        }
    )
    def get(self, request):
        selector = PlaceSelector
        lat_lon = selector.lat_lon()
        serializer = self.MapMarkerOutputSerializer(lat_lon, many=True)

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
    queryset = Place.objects.prefetch_related('place_likeuser_set')
    serializer_class = PlaceSerializer
    permission_classes = [
        AllowAny,
    ]
    pagination_class = BasicPagination

    def filter_if_given(self, qs, query):
        if (query):
            qs = qs.filter(query)
        return qs

    def get_filter_query(self, array):
        query = Q(is_release=True)  # 심사 완료된 장소만 노출
        for a in array:
            if query is None:
                query = Q(category=a)
            else:
                query = query | Q(category=a)
        return query

    def search_if_given(self, search):
        if (search):
            qs = self.get_queryset().filter(Q(place_name__icontains=search))
        else:
            qs = self.get_queryset()
        return qs

    @swagger_auto_schema(operation_id='api_places_place_search_get',
                         manual_parameters=[param_search, param_filter], security=[])
    def get(self, request):
        '''
        search,filter를 적용한 장소 리스트를 distance로 정렬하여 반환
        '''
        search = request.GET.get('search', '')
        qs = self.search_if_given(search)
        array = request.query_params.getlist('filter[]', '배열')
        if array != '배열':
            query = self.get_filter_query(array)
            qs = self.filter_if_given(qs, query)
        serializer = self.get_serializer(
            qs,
            many=True,
            context={
                "left": request.query_params.get("left"),
                "right": request.query_params.get("right"),
                "request": request
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
    permission_classes = [
        AllowAny,
    ]

    @swagger_auto_schema(operation_id='api_places_place_detail_get',
                         manual_parameters=[param_id], security=[])
    def get(self, request):
        '''
            Place의 detail한 정보를 주는 api
        '''
        pk = request.GET.get('id', '')
        place = self.get_queryset().get(id=pk)
        return Response({
            'status': 'success',
            'data': PlaceDetailSerializer(place, context={'request': request}).data,
        }, status=status.HTTP_200_OK)
