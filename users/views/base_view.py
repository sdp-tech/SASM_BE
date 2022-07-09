from ..models import User
from ..serializers import *

from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView

# 회원가입
class SignupView(CreateAPIView):
    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = [
        AllowAny, 
    ]

#나의 정보 조회, 변경, 삭제       
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


#관리자가 유저 정보 확인
@api_view(["GET"])
@permission_classes([IsAdminUser])
def user_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
        return Response(UserSerializer(user).data)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)



# 로그인 함수
@api_view(['POST'])
@permission_classes([AllowAny])
def Login(request):
    if request.method == 'POST':
        print('data 넘어옴')
        serializer = UserLoginSerializer(data=request.data)
        print(serializer)
        
        if not serializer.is_valid(raise_exception=True):
            return Response({"message": "Request Body Error"}, status=status.HTTP_409_CONFLICT)
        
        print("gg",serializer.data)
        # print("gg",serializer{data})
        if serializer.data['email'] == "None":
            return Response({"message": 'fail'}, status=status.HTTP_200_OK)
        response = {
            'success': True,
            'token': serializer.data['token'],
            'nickname' : serializer.data['nickname']
        }
        return Response(response, status=status.HTTP_200_OK)


#이메일 찾기
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

#중복체크
@api_view(["POST"])
@permission_classes([AllowAny])
def rep_check(request):
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
