from ..models import User
from ..serializers import *
from rest_framework import status
from rest_framework.response import Response 
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

#email 인증 관련
import traceback
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework_jwt.settings import api_settings

jwt_decode_handler= api_settings.JWT_DECODE_HANDLER
jwt_payload_get_user_id_handler = api_settings.JWT_PAYLOAD_GET_USER_ID_HANDLER


#비밀번호 재설정 이메일 보내기
class PwResetEmailSendView(APIView):
    permission_classes = [AllowAny]
    
    def post(self,request):
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

class PasswordChangeView(APIView):
    
    model = User
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
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
                        user2 = authenticate(email=user.email, password=serializer.data['password'])
                        if user2 != None :
                            return Response('기존 비밀번호와 일치합니다',status=status.HTTP_400_BAD_REQUEST)
                        user.set_password(serializer.data.get("password"))
                        print(user.password)
                        user.save()
                        response = {
                            'status': 'success',
                            'code': status.HTTP_200_OK,
                            'message': 'Password updated successfully',
                            'data': []
                        }
                        return Response(response)
                    return Response('비밀번호를 다시 입력해주세요',status=status.HTTP_400_BAD_REQUEST)
                return Response('인증에 실패하였습니다',status=status.HTTP_400_BAD_REQUEST)
            return Response('일치하는 유저가 없습니다',status=status.HTTP_400_BAD_REQUEST)           
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)