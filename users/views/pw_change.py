import string
import random
from webbrowser import get
from ..models import User
from ..serializers import *
from rest_framework import status
from rest_framework.response import Response 
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import viewsets
#email 인증 관련
import traceback
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.core.management.utils import get_random_secret_key
from django.contrib.auth import authenticate
from rest_framework_jwt.settings import api_settings
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

jwt_decode_handler= api_settings.JWT_DECODE_HANDLER
jwt_payload_get_user_id_handler = api_settings.JWT_PAYLOAD_GET_USER_ID_HANDLER
def urlsend():
    return redirect('http://localhost:3000/auth/find/SetNewPassword/')
def email_auth_string():
    LENGTH = 5
    string_pool = string.ascii_letters + string.digits
    auth_string = ""
    for i in range(LENGTH):
        auth_string += random.choice(string_pool)
    return auth_string
#비밀번호 재설정 이메일 보내기
class PwResetEmailSendView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        serializer = PwEmailSerializer(data=request.data)
        try:
            if serializer.is_valid():
                user_email = serializer.data['email']
                print(user_email)
                user = User.objects.get(email=user_email)
                print(user)
                payload = JWT_PAYLOAD_HANDLER(user)
                jwt_token = JWT_ENCODE_HANDLER(payload)
                plaintext  = '...'
                code = email_auth_string()
                html_content = render_to_string('users/password_reset.html', {
                    'user': user,
                    'nickname' : user.nickname,
                    'domain': 'api.sasmbe.com',
                    'uid': force_str(urlsafe_base64_encode(force_bytes(user.pk))),
                    'token': jwt_token,
                    'code': code,
                })
                user.code = code
                print('code',code)
                user.save()
                print('유저의 코드',user.code)
                mail_subject = '[SDP] 비밀번호 변경 메일입니다'
                to_email = user.email
                from_email = 'sdpygl@gmail.com'
                msg = EmailMultiAlternatives(mail_subject,plaintext,from_email, [to_email])
                msg.attach_alternative(html_content, "text/html")
                imagefile = 'SASM_LOGO_BLACK.png'
                file_path = os.path.join(settings.BASE_DIR, 'static/img/SASM_LOGO_BLACK.png')
                img_data = open(file_path,'rb').read()
                image = MIMEImage(img_data)
                image.add_header('Content-ID','<{}>'.format(imagefile))
                msg.attach(image)
                msg.send()
                print('전송완료')
                return Response({
                        'status': 'success',
                    }, status=status.HTTP_200_OK)
            print(serializer.errors)
            return Response({
                        'status': 'fail',
                        'data': serializer.errors,
                    }, status=status.HTTP_404_NOT_FOUND)
        except( ValueError, OverflowError, User.DoesNotExist):
            user = None
            print(traceback.format_exc())
            return Response({
                        'status': 'error',
                        'message': 'Unknown',
                        'code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)

#비밀번호 재설정
class PasswordChangeView(viewsets.ModelViewSet):
    
    queryset = User.objects.all()
    serializer_class = PwChangeSerializer
    permission_classes = [AllowAny]
    def get(self,request):
        try:
            return redirect('https://main.d2hps9gsgzjxq.amplifyapp.com/auth/find/SetNewPassword/')
        except:
            return Response({
                        'status': 'error',
                        'message': 'Unknown',
                        'code': 400
                    }, status=status.HTTP_400_BAD_REQUEST) 
    def post(self, request):
        serializer = PwChangeSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            code = serializer.data['code']
            print(code)
            if User.objects.filter(code = code).exists():
                user = User.objects.get(code = code)
                if serializer.data['password']:
                    user2 = authenticate(email=user.email, password=serializer.data['password'])
                    if user2 != None :
                        return Response({
                            'status': 'fail',
                            'data': {"password": "identical to previous password"},
                    }, status=status.HTTP_200_OK)
                    user.set_password(serializer.data.get("password"))
                    new_code = get_random_secret_key()
                    user.code = new_code[0:5]
                    user.save()
                    return Response({
                        'status': 'success',
                    }, status=status.HTTP_200_OK)
                return Response({
                        'status': 'fail',
                        'data': {'password':'Password does not exist'},
                    }, status=status.HTTP_404_NOT_FOUND)
            return Response({
                        'status': 'error',
                        'message': {'code':'Code does not match with database'},
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
        return Response({
                        'status': 'fail',
                        'data': serializer.errors,
                    }, status=status.HTTP_400_BAD_REQUEST)
