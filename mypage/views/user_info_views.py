from rest_framework.views import APIView
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from mypage.services import UserInfoService


class UserGetApi(APIView):
    permission_classes = (IsAuthenticated, )

    class UserGetOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        gender = serializers.CharField()
        nickname = serializers.CharField()
        birthdate = serializers.DateField()
        email = serializers.EmailField()
        address = serializers.CharField()
        profile_image = serializers.ImageField()
        is_sdp_admin = serializers.BooleanField()
        is_verified = serializers.BooleanField()

    @swagger_auto_schema(
        operation_id='나의 정보 조회',
        operation_description='''
            마이페이지에 저장된 나의 정보를 조회합니다.<br/>
            Request시 전달해야 할 파라미터는 없습니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'gender': 'male',
                        'nickname': 'sdpofficial',
                        'birthdate': '2000.03.12',
                        'email': 'sdptech@gmail.com',
                        'address': '서대문구 연세로',
                        'profile_image': 'https://abc.com/1.jpg',
                        'is_sdp_admin': True,
                        'is_verified': False,
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        serializer = self.UserGetOutputSerializer(request.user)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class UserUpdateApi(APIView):
    permission_classes = (IsAuthenticated, )

    class UserUpdateInputSerializer(serializers.Serializer):
        gender = serializers.CharField()
        nickname = serializers.CharField()
        birthdate = serializers.DateField()
        email = serializers.EmailField()
        address = serializers.CharField()
        profile_image = serializers.ImageField()

    @swagger_auto_schema(
        request_body=UserUpdateInputSerializer,
        security=[],
        operation_id='나의 정보를 변경',
        operation_description='''
            마이페이지에 저장된 나의 정보를 변경합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'gender': 'male',
                        'nickname': 'sdpofficial',
                        'birthdate': '2000.03.12',
                        'email': 'sdptech@gmail.com',
                        'address': '서대문구 연세로',
                        'profile_image': 'https://abc.com/1.jpg',
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def patch(self, request):
        serializer = self.UserUpdateInputSerializer(
            data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = UserInfoService(user=request.user)

        update = service.update(
            gender=data.get('gender', None),
            nickname=data.get('nickname', None),
            birthdate=data.get('birthdate', None),
            email=data.get('email', None),
            address=data.get('address', None),
            profile_image=data.get('profile_image', None),
        )

        return Response({
            'status': 'success',
            'data': {'id': update.id},
        }, status=status.HTTP_200_OK)
