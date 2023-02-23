from django.db.models import Q
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import ValidationError
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema

from places.models import Place
from places.selectors import PlaceSelector, PlaceCoordinatorSelector

from rest_framework.views import APIView
from community.mixins import ApiAuthMixin
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class MapMarkerApi(APIView, ApiAuthMixin):
    class MapMarkerOutputSerializer(serializers.Serializer):
        id = serializers.CharField(required=False)
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
                examples = {
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


class PlaceListApi(APIView, ApiAuthMixin):

    class PlaceListFilterSerializer(serializers.Serializer):
        left = serializers.FloatField()
        right = serializers.FloatField()
        search = serializers.CharField(required=False)
        category = serializers.ListField(required=False)
        

    class PlaceListOutputSerializer(serializers.Serializer):
        id = serializers.CharField(required=False)
        place_name = serializers.CharField(required=False)
        category = serializers.CharField(required=False)
        open_hours = serializers.CharField(required=False)
        place_review = serializers.CharField()
        address = serializers.CharField()
        rep_pic = serializers.CharField(required=False)
        latitude = serializers.FloatField(required=False)
        longitude = serializers.FloatField(required=False)
        place_like = serializers.CharField(required=False) # "ok" or "none"
        distance = serializers.FloatField(required=False)
        

    @swagger_auto_schema(
        operation_id='',
        operation_description='''
            place의 list의 정보를 주는 API
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples = {
                    "application/json": {
                        'id': 1,
                        'place_name': '비건마마',
                        'category': '식당 및 카페',
                        'open_hours': '11:00',
                        'place_review': '전국 최초 비건 카페',
                        'address': '서울 강남구 연세로 111',
                        'rep_pic': 'https://sasm-bucket.com/123.png',
                        'latitue': '15.0',
                        'longitude': '45.2',
                        'place_like': 'ok',
                        'distance': 564.234566,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            )
        }
    )
    def get(self, request):
        filters_serializer = self.PlaceListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = PlaceCoordinatorSelector

        place_list = selector.list(
            user= request.user.id,
            search=filters.get('search', ''),
            category =request.query_params.getlist('filter[]', '배열'), # TODO: get by validated data
            left=filters.get('left'),
            right=filters.get('right')
        )
        
        return get_paginated_response(
            pagination_class=BasicPagination,
            serializer_class=self.PlaceListOutputSerializer,
            queryset=place_list,
            request=request,
            view=self
        )


class PlaceDetailApi(APIView, ApiAuthMixin):
    '''
        place의 detail 정보를 주는 API
    '''
    class PlaceDetailOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        place_name = serializers.CharField()
        category = serializers.CharField(required=False)
        open_hours = serializers.CharField(required=False)
        mon_hours = serializers.CharField()
        tues_hours = serializers.CharField()
        mon_hours = serializers.CharField()
        wed_hours = serializers.CharField()
        thurs_hours = serializers.CharField()
        fri_hours = serializers.CharField()
        sat_hours = serializers.CharField()
        sun_hours = serializers.CharField()
        place_review = serializers.CharField()
        address = serializers.CharField()
        rep_pic = serializers.CharField(required=False)
        short_cur = serializers.CharField(required=False)
        latitude = serializers.FloatField(required=False)
        longitude = serializers.FloatField(required=False)
        photos = serializers.ListField(required=False)
        place_sns_url = serializers.ListField(required=False)
        story_id = serializers.IntegerField(required=False)
        place_like = serializers.CharField(required=False)
        category_statistics = serializers.FloatField(required=False)


    @swagger_auto_schema(
        operation_id='',
        operation_description='''
            place의 list의 정보를 주는 API
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples = {
                    "application/json": {
                    "id": 1,
                    "place_name": "비건마마",
                    "category": "식당 및 카페",
                    "open_hours": "9:00",
                    "mon_hours": "9:00",
                    "tues_hours": "9:00",
                    "wed_hours": "9:00",
                    "thurs_hours": "9:00",
                    "fri_hours": "9:00",
                    "sat_hours": "9:00",
                    "sun_hours": "9:00",
                    "place_review": "국내 최초 비건 카페",
                    'address': '서울 강남구 연세로 111',
                    'rep_pic': 'https://sasm-bucket.com/123.png',
                    'short_cur': "",
                    'latitue': '15.0',
                    'longitude': '45.2',
                    "photos": [
                            {
                                "image": 'https://sasm-bucket.com/456.png'
                             },
                             {
                                "image": 'https://sasm-bucket.com/789.png'
                             },
                    ],
                    "place_sns_url" : [
                            {
                                "url": "https://www.sasm.co.kr"
                             }
                    ],
                    "story_id": 1,
                    "place_like": "ok",
                    "category_statistics": []
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            )
        }
    )
    def get(self,request):
        '''
            Place의 detail한 정보를 주는 api
        '''
        selector = PlaceCoordinatorSelector

        # place_id = request.GET.get('id', '')
        place = selector.detail(
            user= request.user.id,
            place_id=request.query_params.get('id'))

        serializer = self.PlaceDetailOutputSerializer(place)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)