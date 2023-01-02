import traceback

from functools import partial
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from places.serializers import PlaceSerializer
from stories.serializers import StoryListSerializer
from ..models import User
from places.models import Place
from stories.models import Story
from users.serializers import UserSerializer, UserLoginSerializer, EmailFindSerializer, RepetitionCheckSerializer, UserLogoutSerializer
from sasmproject.swagger import param_filter

# serializer에 partial=True를 주기위한 Mixin


class SetPartialMixin:
    def get_serializer_class(self, *args, **kwargs):
        serializer_class = super().get_serializer_class(*args, **kwargs)
        return partial(serializer_class, partial=True)


class PlaceLikePagination(PageNumberPagination):
    page_size = 6
    #page_size_query_param = 'page_size'


class UserPlaceLikeView(viewsets.ModelViewSet):
    '''
    user가 좋아요 한 장소 정보를 가져오는 API
    '''
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [
        IsAuthenticated,
    ]
    pagination_class = PlaceLikePagination

    @swagger_auto_schema(operation_id='api_users_like_place_get', manual_parameters=[param_filter])
    def get(self, request):
        user = request.user
        # 역참조 이용
        like_place = user.PlaceLikeUser.all()
        array = request.query_params.getlist('filter[]', '배열')
        query = None
        if array != '배열':
            for a in array:
                if query is None:
                    query = Q(category=a)
                else:
                    query = query | Q(category=a)
            place = like_place.filter(query)
            page = self.paginate_queryset(place)
        else:
            page = self.paginate_queryset(like_place)
        # context 값 넘겨주기
        if page is not None:
            serializer = self.get_paginated_response(self.get_serializer(
                page, many=True, context={'request': request, "left": 0, "right": 0}).data)
        else:
            serializer = self.get_serializer(page, many=True, context={
                                             'request': request, "left": 0, "right": 0})
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class StoryLikePagination(PageNumberPagination):
    page_size = 4
    #page_size_query_param = 'page_size'


class UserStoryLikeView(viewsets.ModelViewSet):
    '''
    user가 좋아요 한 스토리 정보를 가져오는 API
    '''
    queryset = Story.objects.all()
    serializer_class = StoryListSerializer
    permission_classes = [
        IsAuthenticated,
    ]
    pagination_class = StoryLikePagination

    @swagger_auto_schema(operation_id='api_users_like_story_get', manual_parameters=[param_filter])
    def get(self, request):
        user = request.user
        # 역참조 이용
        like_story = user.StoryLikeUser.all()
        array = request.query_params.getlist('filter[]', '배열')
        query = None
        if array != '배열':
            for a in array:
                if query is None:
                    query = Q(address__category=a)
                else:
                    query = query | Q(address__category=a)
            story = like_story.filter(query)
            page = self.paginate_queryset(story)
        else:
            page = self.paginate_queryset(like_story)
        # context 값 넘겨주기
        if page is not None:
            serializer = self.get_paginated_response(self.get_serializer(
                page, many=True, context={'request': request}).data)
        else:
            serializer = self.get_serializer(
                page, many=True, context={'request': request})
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

# SetPartialMixin 상속


@method_decorator(name='post', decorator=swagger_auto_schema(
    operation_id='api_users_signup_post', security=[]))
class SignupView(SetPartialMixin, CreateAPIView):
    '''
    회원가입을 수행하는 API
    '''

    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = [
        AllowAny,
    ]

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({
            'status': 'Success',
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    '''
        나의 정보를 조회, 변경, 삭제 하는 API
        ---
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'status': 'success',
            'data': UserSerializer(request.user).data,
        }, status=status.HTTP_200_OK)

# TODO: refactor - 파라미터를 기존 type, email/nickname에서 type, value로 바꾸기

    def post(self, request):
        serializer = UserSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid():
            # email 수정 시 reject
            if 'email' in serializer.validated_data:
                return Response({
                    'status': 'fail',
                    'message': '이메일은 변경할 수 없습니다.',
                }, status=status.HTTP_400_BAD_REQUEST)

            # 중복된 닉네임 수정 시 reject
            if 'nickname' in serializer.validated_data:
                try:
                    nickname = serializer.validated_data['nickname']
                    if check_email_nickname_rep('nickname', nickname):
                        return Response({
                            'status': 'fail',
                            'message': '이미 사용 중인 닉네임입니다.',
                        }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        'status': 'error',
                        'message': 'Unknown',
                        'code': 400,
                    }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()

            if 'nickname' in serializer.validated_data:  # nickname이 변경되었을 경우
                return Response({
                    'status': 'success',
                    'data': {"nickname": serializer.validated_data['nickname']},
                }, status=status.HTTP_200_OK)

            else:
                return Response({
                    'status': 'success',
                }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'fail',
                'data': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response({
            'status': 'success',
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def user_detail(request, pk):
    '''
        관리자가 유저 정보를 확인하는 API
    '''
    try:
        user = User.objects.get(pk=pk)
        return Response({
            'status': 'success',
            'data': UserSerializer(user).data,
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'User does not exist',
            'code': 404
        }, status=status.HTTP_404_NOT_FOUND)


class LoginView(GenericAPIView):
    '''
        로그인 API
    '''
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            if serializer.validated_data['email'] == "None":
                return Response({
                    'status': 'error',
                    'message': 'Email does not exist',
                    'code': 404
                }, status=status.HTTP_404_NOT_FOUND)

            print("login 확인", serializer.validated_data['access'])
            response = {
                'access': serializer.validated_data['access'],
                'refresh': serializer.validated_data['refresh'],
                'nickname': serializer.validated_data['nickname']
            }
            return Response({
                'status': 'success',
                'data': response,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'fail',
                'message': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(GenericAPIView):
    '''
        로그아웃 API
    '''
    serializer_class = UserLogoutSerializer
    permission_classes = (IsAuthenticated,)
    queryset = User.objects.all()

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def findemail(request):
    serializer = EmailFindSerializer(data=request.data)
    print(request.data)
    if serializer.is_valid():
        if User.objects.filter(email=serializer.data['email']).exists():
            data = '존재하는 이메일입니다'
        else:
            data = '존재하지 않는 이메일입니다'
        print(data)
        return Response({
            'status': 'success',
            'data': data,
        }, status=status.HTTP_200_OK)
    return Response({
                    'status': 'fail',
                    'data': serializer.errors,
                    }, status=status.HTTP_400_BAD_REQUEST)

# TODO: refactor - 파라미터를 기존 type, email/nickname에서 type, value로 바꾸기


@api_view(["POST"])
@permission_classes([AllowAny])
def rep_check(request):
    '''
    중복 체크를 수행하는 API
    '''
    try:
        type = request.data['type']
        if type == 'email':
            value = request.data['email']
        elif type == 'nickname':
            value = request.data['nickname']

        if check_email_nickname_rep(type, value):
            if type == 'email':
                data = '이미 사용 중인 이메일입니다.'
            elif type == 'nickname':
                data = '이미 사용 중인 닉네임입니다.'
        else:
            if type == 'email':
                data = '사용 가능한 이메일입니다.'
            elif type == 'nickname':
                data = '사용 가능한 닉네임입니다.'
        return Response({
            'status': 'success',
            'data': data,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(str(e))
        traceback.print_exc()
        return Response({
                        'status': 'error',
                        'message': 'Unknown',
                        'code': 400,
                        }, status=status.HTTP_400_BAD_REQUEST)

# TODO: refactor - 파라미터를 기존 type, email/nickname에서 type, value로 바꾸기


def check_email_nickname_rep(type, value):
    if type == 'email':
        data = {'type': type, 'email': value}
    elif type == 'nickname':
        data = {'type': type, 'nickname': value}

    serializer = RepetitionCheckSerializer(data=data)

    if serializer.is_valid():
        type = serializer.data['type']
        if type == 'email':
            if User.objects.filter(email=serializer.data['email']).exists():
                return True
            else:
                return False
        elif type == 'nickname':
            if User.objects.filter(nickname=serializer.data['nickname']).exists():
                return True
            else:
                return False
    else:
        raise Exception('data validation fails')
