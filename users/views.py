from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework import status
from .models import User
from .serializers import *
from django.contrib.auth import get_user_model
from rest_framework import generics
#email 인증 관련
from django.utils.encoding import force_str
from rest_framework_jwt.settings import api_settings
from django.utils.http import urlsafe_base64_decode
import traceback
jwt_decode_handler= api_settings.JWT_DECODE_HANDLER
jwt_payload_get_user_id_handler = api_settings.JWT_PAYLOAD_GET_USER_ID_HANDLER

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


#로그인
@api_view(['POST'])
@permission_classes([AllowAny])
def Login(request):
    if request.method == 'POST':
        serializer = UserLoginSerializer(data=request.data)

        if not serializer.is_valid(raise_exception=True):
            return Response({"message": "Request Body Error"}, status=status.HTTP_409_CONFLICT)
        if serializer.validated_data['email'] == "None":
            return Response({"message": 'fail'}, status=status.HTTP_200_OK)
        response = {
            'success': True,
            'token': serializer.data['token']
        }
        return Response(response, status=status.HTTP_200_OK)

#회원가입 후 이메일로 유저 activate
class UserActivateView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, uid, token):
        try:
            real_uid = force_str(urlsafe_base64_decode(uid))
            print(real_uid)
            user = User.objects.get(pk=real_uid)
            if user is not None:
                payload = jwt_decode_handler(token)
                user_id =jwt_payload_get_user_id_handler(payload)
                print(type(user))
                print(type(user_id))
                if int(real_uid) == int(user_id):
                    user.is_active = True
                    user.save()
                    return Response(user.email + '계정이 활성화 되었습니다', status=status.HTTP_200_OK)
                return Response('인증에 실패하였습니다', status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('인증에 실패하였습니다', status=status.HTTP_400_BAD_REQUEST)

        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            print(traceback.format_exc())
            return Response('인증에 실패하였습니다',status=status.HTTP_400_BAD_REQUEST)

#비밀번호 재설정 이메일 보내기
class PwResetEmailSendView(APIView):
    permission_classes = [AllowAny]
    
    def put(self,request):
        serializer = PwEmailSerializer(data=request.data)
        try:
            if serializer.is_valid():
                user_email = serializer.data['email']
                print(user_email)
                user = User.objects.get(email = user_email)
                print(user)
                payload = JWT_PAYLOAD_HANDLER(user)
                jwt_token = JWT_ENCODE_HANDLER(payload)
                message = render_to_string('users/password_reset.html', {
                    'user': user,
                    'domain': 'localhost:8000',
                    'uid': force_str(urlsafe_base64_encode(force_bytes(user.pk))),
                    'token': jwt_token,
                })
                print(message)
                mail_subject = '[SDP] 비밀번호 변경 메일입니다'
                to_email = user.email
                email = EmailMessage(mail_subject, message, to = [to_email])
                email.send()    
                return Response( user.email+ '이메일 전송이 완료되었습니다',status=status.HTTP_200_OK)
            print(serializer.errors)
            return Response('일치하는 유저가 없습니다',status=status.HTTP_400_BAD_REQUEST)
        except( ValueError, OverflowError, User.DoesNotExist):
            user = None
            print(traceback.format_exc())
            return Response('일치하는 유저가 없습니다',status=status.HTTP_400_BAD_REQUEST)

#비밀번호 재설정
#아직 원래 비밀번호랑 비교 하는거 없음
class PasswordChangeView(APIView):
    
    model = User
    permission_classes = [AllowAny]

    def put(self, request, uid, token):
        serializer = PwChangeSerializer(data=request.data)
        if serializer.is_valid():
            real_uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=real_uid)
            if user is not None:
                payload = jwt_decode_handler(token)
                user_id =jwt_payload_get_user_id_handler(payload)
                if int(real_uid) == int(user_id):
                    print("비밀번호")
                    print(user.password)
                    print(serializer.data['password'])
                    if serializer.data['password']:
                        user.set_password(serializer.data.get("password"))
                        user.save()
                        response = {
                            'status': 'success',
                            'code': status.HTTP_200_OK,
                            'message': 'Password updated successfully',
                            'data': []
                        }
                        return Response(response)
                    return Response('기존 비밀번호와 일치합니다',status=status.HTTP_400_BAD_REQUEST)
                return Response('인증에 실패하였습니다',status=status.HTTP_400_BAD_REQUEST)
            return Response('일치하는 유저가 없습니다',status=status.HTTP_400_BAD_REQUEST)           
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#이메일 찾기
@api_view(["PUT"])
@permission_classes([AllowAny])
def findemail(request):
    serializer = EmailFindSerializer(data=request.data)
    if serializer.is_valid():
        if User.objects.filter(email=serializer.data['email']).exists():
            return Response('존재하는 이메일입니다')
        else:
            return Response('존재하지 않는 이메일입니다')
    return Response('이메일을 다시 입력하세요')