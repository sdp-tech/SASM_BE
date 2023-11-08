from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound, ValidationError

from core.views import get_paginated_response

from users.models import User

from places.models import PlaceVisitorReview, Place

import users

from mypage.selectors.places_selectors import UserReviewedPlaceSelector, MyPlaceSearchSelector

from core.views import get_paginated_response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

#리뷰 작성한 장소 리스트룰 반환하는 API
class UserReviewedPlaceGetApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class UserReviewedGetSerializer(serializers.ModelSerializer):

        id = serializers.IntegerField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        rep_pic = serializers.ImageField()
        address = serializers.CharField()


        class Meta:
            model = Place
            fields = ['id', 'place_name','category','rep_pic','address']

    @swagger_auto_schema(
        operation_id='내가 리뷰 작성한 장소 조회',
        operation_description='''
                내가 리뷰 작성한 장소를 조회합니다. 쿼리 파라미터 : 없음 <br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "id": 1,
                        "place_name": "타이거릴리",
                        "category": "제로웨이스트 샵",
                        "rep_pic": "https://sasm-bucket.s3.amazonaws.com/media/%ED%83%80%EC%9D%B4%EA%B1%B0%EB%A6%B4%EB%A6%AC.jpeg",
                        "address": "서울 마포구 포은로 119 1층"
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )

    def get(self,request):
        self.user = request.user

        selector = UserReviewedPlaceSelector(self.user)
        places = selector.list()

        serializer = self.UserReviewedGetSerializer(places, many=True)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserReviewedGetSerializer,
            queryset=places,
            request=request,
            view=self
        )
    

class OtherUserReviewedPlaceGetApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class OtherUserReviewedGetSerializer(serializers.ModelSerializer):

        id = serializers.IntegerField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        rep_pic = serializers.ImageField()
        address = serializers.CharField()


        class Meta:
            model = Place
            fields = ['id', 'place_name','category','rep_pic','address']

    @swagger_auto_schema(
        operation_id='타유저가 리뷰 작성한 장소 조회',
        operation_description='''
                타유저가 리뷰 작성한 장소를 조회합니다. 쿼리 파라메터로 'email' 필요(타겟 유저의 이메일)<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "id": 1,
                        "place_name": "타이거릴리",
                        "category": "제로웨이스트 샵",
                        "rep_pic": "https://sasm-bucket.s3.amazonaws.com/media/%ED%83%80%EC%9D%B4%EA%B1%B0%EB%A6%B4%EB%A6%AC.jpeg",
                        "address": "서울 마포구 포은로 119 1층"
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )

    def get(self,request):
        target_email = request.query_params.get('email')
            
        if not target_email:
            raise ValidationError(detail="이메일 쿼리 파라메터 필요")
                
        try:
            self.user = User.objects.get(email=target_email)
        except User.DoesNotExist:
            raise NotFound(detail="유저를 찾을 수 없음")

        selector = UserReviewedPlaceSelector(self.user)
        places = selector.list()

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OtherUserReviewedGetSerializer,
            queryset=places,
            request=request,
            view=self
        )


#좋아요한 장소에서 검색하는 API
class MyPlaceSearchApi(APIView):

    permission_classes = (IsAuthenticated, )

    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class MyPlaceListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        filter = serializers.ListField(required=False)
    
    class MyPlaceListOutputSerializer(serializers.Serializer):
        id=serializers.IntegerField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        rep_pic = serializers.ImageField()
        address = serializers.CharField()
        created = serializers.DateTimeField()

        def get_place_name(self, obj):
            return obj.place.place_name
        
        def get_place_like(self, obj):
            re_user = self.context['request'].user
            likes = users.selector.get_user_like_place(re_user)
            return likes
    
    @swagger_auto_schema(
        operation_id='마이 플레이스 서치',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 장소 리스트를 반환합니다. 쿼리 파라미터 : search, filter <br/>
            ''',
        query_serializer=MyPlaceListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'category': '녹색 공간',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'created': '2023-08-24T14:15:22Z',
                        'address' : '서울 마포구 포은로 119 1층',
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.MyPlaceListFilterSerializer(
            data = request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = MyPlaceSearchSelector(user = request.user)
        like_place = selector.list(
            search = filters.get('search', ''),
            filter = filters.get('filter', []),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.MyPlaceListOutputSerializer,
            queryset=like_place,
            request=request,
            view=self,
        )