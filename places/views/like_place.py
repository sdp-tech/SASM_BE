from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers

from places.models import Place
from places.serializers import PlaceSerializer
from places.services import PlaceService
from places.selectors import PlaceCoordinatorSelector
from users.models import User
from users.serializers import UserSerializer
from sasmproject.swagger import PlaceLikeView_post_params

from rest_framework.views import APIView
from community.mixins import ApiAuthMixin
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class PlaceLikeApi(APIView, ApiAuthMixin):
    class PlaceLikeOutputSerializer(serializers.Serializer):
        id = serializers.CharField()
        gender = serializers.CharField(required=False)
        nickname = serializers.CharField(required=False)
        birthdate = serializers.CharField(required=False)
        email = serializers.CharField()
        address = serializers.CharField()
        profile_image = serializers.CharField()
        is_sdp = serializers.BooleanField()

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
                    "id": 1,
                    "gender": "female",
                    "nickname": "스드프",
                    "birthdate": "2023-02-23",
                    "email": "sdpygl@gmail.com",
                    "address": "강남구 연세로1",
                    "profile_image": "https://sasm-bucket.com/media/profile.png",
                    "is_sdp": False
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            )
        }
    )

    def get(self, request, pk):
        selector = PlaceCoordinatorSelector

        likers = selector.likers(place_id=pk)
        
        serializer = self.PlaceLikeOutputSerializer(likers, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        '''
            좋아요 및 좋아요 취소를 수행하는 api
        '''
        place_id = request.data['id']
        user = request.user

        service = PlaceService

        if request.user.is_authenticated:
            service.like_or_dislike(
                user=user,
                place_id=place_id
            )
            return Response({
                "status" : "success",
            },status=status.HTTP_200_OK)
        else:
            return Response({
            'status': 'fail',
            'data' : { "user" : "user is not authenticated"},
        }, status=status.HTTP_401_UNAUTHORIZED)