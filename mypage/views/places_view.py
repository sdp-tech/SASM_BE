from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny


from places.models import PlaceVisitorReview, Place
import traceback

from mypage.selectors.places_selectors import UserReviewedSelector

from core.views import get_paginated_response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class UserReviewedGetApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class UserReviewedGetSerializer(serializers.ModelSerializer):

        place_id = serializers.IntegerField()
        place_name = serializers.CharField(source='place.place_name')
        category = serializers.CharField(source='place.category')
        contents = serializers.CharField()
        rep_pic = serializers.ImageField(source='place.rep_pic')
        address = serializers.CharField(source='place.address')


        class Meta:
            model = PlaceVisitorReview
            fields = ['place_id', 'place_name','category','contents','rep_pic','address']

    @swagger_auto_schema(
        operation_id='리뷰 작성한 장소 조회',
        operation_description='''
                유저가 리뷰 작성한 장소를 조회합니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "place_id": 1,
                        "place_name": "타이거릴리",
                        "category": "제로웨이스트 샵",
                        "contents": "마포에 있는 흔치 않은 제로 웨이스트 샵입니다. 구경하다보면 시간 가는줄 모를 정도입니다!",
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
        try:
            self.user = request.user

            selector = UserReviewedSelector(self.user)
            places = selector.list()
                
            serializer = self.UserReviewedGetSerializer(places,many=True)
            return Response({
                'sataus':'success',
                'data':serializer.data,
            },status=status.HTTP_200_OK)
        
        except Exception as e:
            print("오류가 발생했습니다.")
            print(traceback.format_exc())
            return Response({'status': 'error', 'message': '오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)