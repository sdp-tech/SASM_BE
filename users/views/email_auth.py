from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response 
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from users.models import User
from ..serializers import *

#email 인증 관련
import traceback
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework_jwt.settings import api_settings

jwt_decode_handler= api_settings.JWT_DECODE_HANDLER
jwt_payload_get_user_id_handler = api_settings.JWT_PAYLOAD_GET_USER_ID_HANDLER

class UserActivateView(APIView):
    '''
        회원가입 후 이메일로 유저 activate 하는 API
    '''
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
                    return redirect('http://localhost:3000/auth')
                return Response({
                        'status': 'error',
                        'message': 'signup URL expired',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({
                        'status': 'error',
                        'message': 'User does not exist',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)

        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            print(traceback.format_exc())
            return Response({
                        'status': 'error',
                        'message': 'Unknown',
                        'code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)