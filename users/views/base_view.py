from functools import partial
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from places.serializers import PlaceSerializer
from stories.serializers import StoryListSerializer
from ..models import User
from places.models import Place
from stories.models import Story
from users.serializers import UserSerializer, UserLoginSerializer,EmailFindSerializer,RepetitionCheckSerializer, UserLogoutSerializer

class PlaceLikePagination(PageNumberPagination):
    page_size = 6
    #page_size_query_param = 'page_size'

class UserPlaceLikeView(viewsets.ModelViewSet):
    '''
    user가 좋아요 한 장소 정보를 가져오는 API
    '''
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes=[
        IsAuthenticated,
    ]
    pagination_class=PlaceLikePagination

    def get(self,request):
        user = request.user
        print(user)
        #역참조 이용
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
        #context 값 넘겨주기
        if page is not None:
            serializer = self.get_paginated_response(self.get_serializer(page, many=True,context={'request': request}).data) 
        else:
            serializer = self.get_serializer(page, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class StoryLikePagination(PageNumberPagination):
    page_size = 4
    #page_size_query_param = 'page_size'
    
class UserStoryLikeView(viewsets.ModelViewSet):
    '''
    user가 좋아요 한 스토리 정보를 가져오는 API
    '''
    queryset = Story.objects.all()
    serializer_class = StoryListSerializer
    permission_classes=[
        IsAuthenticated,
    ]
    pagination_class=StoryLikePagination

    def get(self,request):
        user = request.user
        #역참조 이용
        like_story = user.StoryLikeUser.all()
        array = request.query_params.getlist('filter[]', '배열')
        query = None
        if array != '배열':
            for a in array: 
                if query is None: 
                    query = Q(category=a) 
                else: 
                    query = query | Q(category=a)
            story = like_story.filter(query)
            page = self.paginate_queryset(story)
        else:
            page = self.paginate_queryset(like_story)
        #context 값 넘겨주기
        if page is not None:
            serializer = self.get_paginated_response(self.get_serializer(page, many=True,context={'request': request}).data) 
        else:
            serializer = self.get_serializer(page, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

#serializer에 partial=True를 주기위한 Mixin
class SetPartialMixin:
    def get_serializer_class(self, *args, **kwargs):
        serializer_class = super().get_serializer_class(*args, **kwargs)
        return partial(serializer_class, partial=True)

#SetPartialMixin 상속
class SignupView(SetPartialMixin,CreateAPIView):
    '''
    회원가입을 수행하는 API
    '''
    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = [
        AllowAny, 
    ]
class MeView(APIView):
    '''
        나의 정보를 조회, 변경, 삭제 하는 API
        ---
    '''
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def post(self, request):
        print(request.data)
        serializer = UserSerializer(request.user,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
        
            if 'nickname' in serializer.validated_data: #nickname이 변경되었을 경우
                return Response({"nickname": serializer.validated_data['nickname']})
            else:
                return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(["GET"])
@permission_classes([IsAdminUser])
def user_detail(request, pk):
    '''
        관리자가 유저 정보를 확인하는 API
    '''
    try:
        user = User.objects.get(pk=pk)
        return Response(UserSerializer(user).data)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)


class LoginView(GenericAPIView):
    '''
        로그인 API
    '''
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid(raise_exception=True):
            return Response({"message":"Request Body Error"},status=status.HTTP_409_CONFLICT)

        if serializer.validated_data['email'] == "None":
            return Response({"message":'fail'},status=status.HTTP_200_OK)

        print("login 확인", serializer.validated_data['access'])
        response = {
            'success': True,
            'access': serializer.validated_data['access'],
            'refresh': serializer.validated_data['refresh'],
            'nickname' : serializer.validated_data['nickname']
        }
        return Response(response, status=status.HTTP_200_OK)

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
        response = {
            'msg': 'success'
           }
        return Response(response, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([AllowAny])
def findemail(request):
    serializer = EmailFindSerializer(data=request.data)
    if serializer.is_valid():
        if User.objects.filter(email=serializer.data['email']).exists():
            return Response('존재하는 이메일입니다')
        else:
            return Response('존재하지 않는 이메일입니다')
    return Response('이메일을 다시 입력하세요')

@api_view(["POST"])
@permission_classes([AllowAny])
def rep_check(request):
    '''
    중복 체크를 수행하는 API
    '''
    serializer = RepetitionCheckSerializer(data=request.data)
    if serializer.is_valid():
        type = serializer.data['type']
        if type == 'email':
            if User.objects.filter(email=serializer.data['email']).exists():
                return Response('존재하는 이메일입니다')
            else :
                return Response('존재하지 않는 이메일입니다',status=status.HTTP_200_OK)
        elif type == 'nickname':
            if User.objects.filter(nickname=serializer.data['nickname']).exists():
                return Response('존재하는 닉네임입니다')
            else:
                return Response('존재하지 않는 닉네임입니다',status=status.HTTP_200_OK)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
