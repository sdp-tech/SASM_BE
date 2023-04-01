from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from users.mixins import ApiAuthMixin, ApiAdminAuthMixin, ApiAllowAnyMixin
from users.services import UserService, UserPasswordService
from users.selectors import UserSelector

from core.views import get_paginated_response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class UserGetApi(APIView, ApiAuthMixin):
    class UserGetOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        gender = serializers.CharField()
        nickname = serializers.CharField()
        birthdate = serializers.CharField()
        email = serializers.EmailField()
        address = serializers.CharField()
        profile_image = serializers.ImageField()
        is_sdp = serializers.BooleanField()

    def get(self, request):
        serializer = self.UserGetOutputSerializer(request.user)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class UserLoginApi(APIView, ApiAllowAnyMixin):
    permission_classes = (AllowAny,)

    class UserLoginInputSerializer(serializers.Serializer):
        email = serializers.CharField()
        password = serializers.CharField()

    class UserLoginOutputSerializer(serializers.Serializer):
        email = serializers.CharField()
        refresh = serializers.CharField()
        access = serializers.CharField()
        nickname = serializers.CharField(allow_blank=True)

    def post(self, request):
        input_serializer = self.UserLoginInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        service = UserService()

        login_data = service.login(
            email=data.get('email'),
            password=data.get('password'),
        )

        output_serializer = self.UserLoginOutputSerializer(data=login_data)
        output_serializer.is_valid(raise_exception=True)

        return Response({
            'status': 'success',
            'data': output_serializer.data,
        }, status=status.HTTP_200_OK)


class UserLogoutApi(APIView, ApiAuthMixin):
    class UserLogoutSerializer(serializers.Serializer):
        refresh = serializers.CharField()

    def post(self, request):
        serializer = self.UserLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = UserService()

        service.logout(
            refresh=data.get('refresh')
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class EmailCheckApi(APIView):
    permission_classes = (AllowAny,)

    class EmailCheckSerializer(serializers.Serializer):
        email = serializers.EmailField()

    def post(self, request):
        serializer = self.EmailCheckSerializer(data=request.data)
        serializer.is_valid()
        data = serializer.validated_data

        service = UserService()

        check_email_message = service.check_email(
            email=data.get('email')
        )

        return Response({
            'status': 'success',
            'data': check_email_message,
        }, status=status.HTTP_200_OK)


class RepCheckApi(APIView):
    permission_classes = (AllowAny,)

    class RepCheckSerializer(serializers.Serializer):
        type = serializers.CharField(required=False)
        value = serializers.CharField(required=False)

    def post(self, request):
        serializer = self.RepCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = UserService()

        check_rep_message = service.check_rep(
            type=data.get('type'),
            value=data.get('value'),
        )

        return Response({
            'status': 'success',
            'data': check_rep_message,
        }, status=status.HTTP_200_OK)


class UserPlaceLikeApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class PlaceListFilterSerializer(serializers.Serializer):
        filter = serializers.ListField()

    class UserPlaceLikeOuputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        rep_pic = serializers.ImageField()
        place_like = serializers.SerializerMethodField()

        def get_place_like(self, obj):
            return 'ok'

    def get(self, request):
        filter = request.query_params.getlist('filter[]', None)
        # filter_serializer = self.PlaceListFilterSerializer(data=request.query_params)
        # filter_serializer.is_valid()
        # filter = filter_serializer.validated_data

        selector = UserSelector()
        place_list = selector.get_user_like_place(request.user)
        filter_place_list = selector.filter_place_by_query(filter, place_list)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserPlaceLikeOuputSerializer,
            queryset=filter_place_list,
            request=request,
            view=self
        )


class UserStoryLikeApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class StoryListFilterSerializer(serializers.Serializer):
        category = serializers.ListField()

    class UserStoryLikeOuputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        preview = serializers.CharField()
        place_name = serializers.SerializerMethodField()
        rep_pic = serializers.ImageField()
        created = serializers.DateTimeField()
        category = serializers.SerializerMethodField()
        views = serializers.IntegerField()
        story_like = serializers.SerializerMethodField()

        def get_place_name(self, obj):
            return obj.address.place_name

        def get_story_like(self, obj):
            return 'ok'

        def get_category(self, obj):
            return obj.address.category

    def get(self, request):
        filter = request.query_params.getlist('filter[]', None)
        # filter_serializer = self.StoryListFilterSerializer(data=request.query_params)
        # filter_serializer.is_valid()
        # filter = filter_serializer.validated_data

        selector = UserSelector()
        story_list = selector.get_user_like_story(request.user)
        filter_story_list = selector.filter_story_by_query(filter, story_list)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserStoryLikeOuputSerializer,
            queryset=filter_story_list,
            request=request,
            view=self
        )


class PasswordResetSendEmailApi(APIView):
    permission_classes = (AllowAny,)

    class PwEmailSerializer(serializers.Serializer):
        email = serializers.EmailField()

    def post(self, request):
        serializer = self.PwEmailSerializer(data=request.data)
        serializer.is_valid()
        data = serializer.validated_data

        service = UserPasswordService()
        service.password_reset_send_email(email=data.get('email'))

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class PasswordResetApi(APIView):
    permission_classes = (AllowAny,)

    class PwResetInputSerializer(serializers.Serializer):
        code = serializers.CharField(max_length=5)
        password = serializers.CharField()

    @swagger_auto_schema(
        request_body=PwResetInputSerializer,
        security=[],
        operation_id='유저 비밀번호 초기화',
        operation_description='''
            유저가 비밀번호 찾기를 통해 새로운 비밀번호로 초기화하는 API입니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success"
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def put(self, request):
        serializer = self.PwResetInputSerializer(data=request.data)
        serializer.is_valid()
        data = serializer.validated_data

        service = UserPasswordService()

        service.password_change_with_code(
            code=data.get('code'),
            password=data.get('password'),
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class PasswordChangeApi(APIView):
    permission_classes = (IsAuthenticated,)

    class PwChangeInputSerializer(serializers.Serializer):
        password = serializers.CharField()

    @swagger_auto_schema(
        request_body=PwChangeInputSerializer,
        security=[],
        operation_id='유저 비밀번호 변경',
        operation_description='''
            유저가 로그인한 상태에서 비밀번호를 변경하고자 하는 경우 사용할 수 있는 API입니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success"
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def put(self, request):
        serializer = self.PwChangeInputSerializer(data=request.data)
        serializer.is_valid()
        data = serializer.validated_data

        service = UserPasswordService()

        service.password_change(
            user=request.user,
            password=data.get('password'),
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


# class UserUpdateApi(APIView, ApiAuthMixin):
#     class UserUpdateInputSerializer(serializers.Serializer):
#         profile_image = serializers.ImageField()
#         password = serializers.CharField()
#         nickname = serializers.CharField()
#         address = serializers.CharField()
#         birthdate = serializers.CharField()
#         gender = serializers.CharField()

#     # Todo: FE post -> put으로 변경
#     def put(self, request):
#         serializer = self.UserUpdateInputSerializer(data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         data = serializer.validated_data

#         service = UserService(
#             user=request.user
#         )

#         user = service.update(
#             profile_image=data.get('profile_image'),
#             password=data.get('password'),
#             nickname=data.get('nickname'),
#             address=data.get('address'),
#             birthdate=data.get('birthdate'),
#             gender=data.get('gender'),
#         )

#         return Response({
#             'status': 'success',
#             'data': {'id': user.id},
#         }, status=status.HTTP_200_OK)
