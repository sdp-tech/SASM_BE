from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework import status
from .models import User
from .serializers import *
from django.contrib.auth import get_user_model

#email 인증 관련
from django.utils.encoding import force_str
from rest_framework_jwt.settings import api_settings
import traceback
jwt_decode_handler= api_settings.JWT_DECODE_HANDLER
jwt_payload_get_user_id_handler = api_settings.JWT_PAYLOAD_GET_USER_ID_HANDLER

# 함수도 되고 클래스로도 만들 수 있음
class SignupView(CreateAPIView):
    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = [
        AllowAny, #AllowAny - 회원가입할 때는 절대 로그인이 될 수 없는 상황이니까 (아무나 접근 가능)
    ]
            
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


@api_view(["GET"])
def user_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
        return Response(UserSerializer(user).data)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

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