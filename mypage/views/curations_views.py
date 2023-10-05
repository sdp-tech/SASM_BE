
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound, ValidationError

from users.mixins import ApiAuthMixin,  ApiAllowAnyMixin
from mypage.selectors.curations_selectors import CurationSelector
from users.models import User

from core.views import get_paginated_response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class OtherCurationListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class OtherCurationSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer_nickname = serializers.CharField()

    @swagger_auto_schema(
        operation_id='다른 사용자가 작성한 큐레이션 리스트',
        operation_description='''
            email을 받아 해당 유저가 작성한 큐레이션을 리스트합니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '서울 비건카페 탑5',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_nickname': '스드프'
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        target_email = request.query_params.get('email')
            
        if not target_email:
            raise ValidationError(detail="이메일 쿼리 파라메터 필요")
                
        try:
            user = User.objects.get(email=target_email)
        except User.DoesNotExist:
            raise NotFound(detail="유저를 찾을 수 없음")
    
        curations = CurationSelector.my_written_list(user=user)
        serializer = self.OtherCurationSerializer(
            curations, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)




class MyCurationListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class MyCurationSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer_nickname = serializers.CharField()

    @swagger_auto_schema(
        operation_id='마이페이지 내가 작성한 큐레이션 리스트',
        operation_description='''
            내가 작성한 큐레이션을 리스트합니다.<br/>
            request시 전달해야 할 파라미터는 없습니다.
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '서울 비건카페 탑5',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_nickname': '스드프'
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        curations = CurationSelector.my_written_list(user=request.user)
        serializer = self.MyCurationSerializer(
            curations, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class MyLikedCurationListApi(APIView):
    class MyLikedCurationListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)

    class MyLikedCurationListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        rep_pic = serializers.CharField()
        writer_nickname = serializers.CharField()

    @swagger_auto_schema(
        query_serializer=MyLikedCurationListFilterSerializer,
        operation_id='마이페이지 큐레이션 검색 결과 리스트',
        operation_description='''
            유저가 좋아요 한 큐레이션의 검색 결과를 리스트합니다.<br/>
            search(검색어)의 default값은 ''로, 검색어가 없을 시 좋아요 한 모든 큐레이션이 반환됩니다.
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'title': '서울 비건카페 탑5',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'writer_nickname': '스드프'
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.MyLikedCurationListFilterSerializer(
            data=request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        curations = CurationSelector.my_liked_list(
            user=request.user,
            search=filters.get('search', '')
        )

        serializer = self.MyLikedCurationListOutputSerializer(
            curations, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
