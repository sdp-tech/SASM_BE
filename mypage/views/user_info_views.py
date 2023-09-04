from rest_framework.views import APIView
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from mypage.services import UserInfoService
from users.models import User
from mypage.selectors.follow_selectors import UserFollowSelector


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
        introduction = serializers.CharField()

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
                        'introduction' : "안녕하세요",
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
        profile_image = serializers.ImageField()
        introduction = serializers.CharField()

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
                        'profile_image': 'https://abc.com/1.jpg',
                        'introduction' : '안녕하세요',
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
            profile_image=data.get('profile_image', None),
            introduction = data.get('introduction',None),
        )

        return Response({
            'status': 'success',
            'data': {'id': update.id},
        }, status=status.HTTP_200_OK)


class UserWithdrawApi(APIView):
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(
            security=[],
            operation_id='회원 탈퇴하기',
            operation_description='''
                정보 확인을 위해 비밀번호를 체크한 뒤 회원 탈퇴하기를 진행합니다.
            ''',
            responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )

    def delete(self, request):
        UserInfoService.withdraw(
            user=request.user,
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)
    

class OtherUserGetApi(APIView):
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
        introduction = serializers.CharField()
        is_followed = serializers.BooleanField(read_only=True)

        def to_representation(self, instance):
            ret = super().to_representation(instance)
            ret['is_followed'] = UserFollowSelector.follows(source=self.context['request'].user, target=instance)

            return ret

    @swagger_auto_schema(
        operation_id='다른 사용자 정보 조회',
        operation_description='''
            다른 사용자의 정보를 조회합니다.<br/>
            Request시 전달해야 할 파라미터는 다른 사용자의 이메일입니다.<br/>
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
                        'introduction': "안녕하세요",
                        'is_followed' : True,
                    },
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
            "404": openapi.Response(
                description="User Not Found",
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
                
        serializer = self.UserGetOutputSerializer(user, context={'request': request})

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
