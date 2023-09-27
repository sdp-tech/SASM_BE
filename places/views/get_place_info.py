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
from django.shortcuts import get_object_or_404

from places.mixins import ApiAuthMixin
from places.models import Place
from places.serializers import PlaceSerializer, PlaceDetailSerializer
from places.selectors import PlaceSelector
from sasmproject.swagger import param_search, param_filter, param_id
from places.services import *

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
    queryset = Place.objects.prefetch_related('place_likeuser_set', 'photos')
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
        query = None
        for a in array:
            if query is None:
                query = Q(category=a)
            else:
                query = query | Q(category=a)
        return query

    def search_if_given(self, search):
        only_released = Q(is_released=True)  # 심사 완료된 장소만 노출
        if (search):
            qs = self.get_queryset().filter(only_released & Q(place_name__icontains=search))
        else:
            qs = self.get_queryset().filter(only_released)
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


class PlaceDetailView(APIView):
    permission_classes = [AllowAny]

    class PlaceDetailOutputSerializer(serializers.Serializer):
        place_name = serializers.CharField()
        category = serializers.CharField()
        vegan_category = serializers.CharField(allow_null=True)
        tumblur_category = serializers.BooleanField(allow_null=True)
        reusable_con_category = serializers.BooleanField(allow_null=True)
        pet_category = serializers.BooleanField(allow_null=True)
        mon_hours = serializers.CharField()
        tues_hours = serializers.CharField()
        wed_hours = serializers.CharField()
        thurs_hours = serializers.CharField()
        fri_hours = serializers.CharField()
        sat_hours = serializers.CharField()
        sun_hours = serializers.CharField()
        etc_hours = serializers.CharField()
        place_review = serializers.CharField()
        address = serializers.CharField()
        short_cur = serializers.CharField()
        phone_num = serializers.CharField()
        rep_pic = serializers.ImageField()

    @swagger_auto_schema(
        operation_id='',
        operation_description='''
            장소에 대한 상세 정보를 제공하는 API
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 2,
                        'place_name': '안녕 상점',
                        'category': '식당 및 카페',
                        'vegan_category': '비건',
                        'tumblur_category': True,
                        'reusable_con_category': True,
                        'pet_category': True,
                        'mon_hours': '09:00 ~ 22:00',
                        'tues_hours': '09:00 ~ 22:00',
                        'wed_hours': '09:00 ~ 22:00',
                        'thurs_hours': '09:00 ~ 22:00',
                        'fri_hours': '09:00 ~ 22:00',
                        'sat_hours': '09:00 ~ 22:00',
                        'sun_hours': '09:00 ~ 22:00',
                        'etc_hours': '공휴일 09:00 ~ 22:00',
                        'place_review': '\"붉은 벽돌 외관에서의 담소\"',
                        'address': '서울 서대문구 연희로5길 22',
                        'short_cur': '연남장(場) 연희동 카페는 공간이 널찍하고 층고가 높습니다.',
                        'phone_num': '02-3141-7977',
                        'rep_pic': "https://sasm-bucket.s3.amazonaws.com/media/ss_71d59bda2b768ecfc5b41bda9403c00353367069.1920x1080.jpg",
                        "latitude": 1.0,
                        "longitude": 2.0,
                        'imageList': ["https://sasm-bucket.s3.amazonaws.com/media/places/%ED%99%94%EB%A9%B4_%EC%BA%A1%EC%B2%98_2023-04-12_124409.png"],
                        'snsList': [ {"sns_type": 1 , "url" : 'https://instagram.com/abc/'}, 
                                    {"sns_type": 2, 'url':'https://www.sasm.co.kr/'}],
                        "user_liked": True,
                   }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            )
        }
    )
    def get(self, request, place_id):
        try:
            place = PlaceDetailService.get_place_detail(place_id)
            
            user_liked = False
            if request.user.is_authenticated:
                user_liked = place.place_likeuser_set.filter(pk=request.user.pk).exists()
            
            imageList = PlacePhotoService.get_place_photos(place)
            snsList = PlaceSNSUrlService.get_place_sns_urls(place)

            data_to_serialize = {
                'id': place.id,
                'place_name': place.place_name,
                'category': place.category or "",
                'vegan_category': place.vegan_category or None,
                'tumblur_category': place.tumblur_category or False,
                'reusable_con_category': place.reusable_con_category or False,
                'pet_category': place.pet_category or False,
                'mon_hours': place.mon_hours,
                'tues_hours': place.tues_hours,
                'wed_hours': place.wed_hours,
                'thurs_hours': place.thurs_hours,
                'fri_hours': place.fri_hours,
                'sat_hours': place.sat_hours,
                'sun_hours': place.sun_hours,
                'etc_hours': place.etc_hours,
                'place_review': place.place_review,
                'address': place.address,
                'short_cur': place.short_cur,
                'phone_num': place.phone_num,
                'rep_pic': place.rep_pic.url if place.rep_pic else None,
                'latitude': place.latitude,
                'longitude': place.longitude,
                'imageList': imageList,
                'snsList': snsList,
                'user_liked': user_liked,
            }

            return Response({
                'status': 'success',
                'data': data_to_serialize,
            }, status=status.HTTP_200_OK)
        except Place.DoesNotExist as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
