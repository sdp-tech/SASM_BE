from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework import status
from .models import User
from .serializers import *
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
import urllib
from django.conf import settings
from allauth.socialaccount.models import SocialAccount
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google import views as google_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.http import JsonResponse
import requests
from json.decoder import JSONDecodeError

state = getattr(settings, 'STATE')
BASE_URL = 'http://127.0.0.1:8000/'
GOOGLE_CALLBACK_URI = BASE_URL + 'users/google/callback/'
KAKAO_CALLBACK_URI = BASE_URL + 'users/kakao/callback/'

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

# 코드 요청
# def kakao_login(request):
#     app_rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
#     return redirect(
#         f"https://kauth.kakao.com/oauth/authorize?client_id={app_rest_api_key}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code"
#     )
# 
# # 토큰 요청
# def kakao_callback(request):
#     app_rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
#     code = request.GET.get("code")
#     redirect_uri = KAKAO_CALLBACK_URI
#     
#     token_req = requests.get(
#         f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={app_rest_api_key}&redirect_uri={redirect_uri}&code={code}"
#     )
#     token_req_json = token_req.json()
#     error = token_req_json.get("error")
#     if error is not None:
#         raise JSONDecodeError(error)
#     access_token = token_req_json.get("access_token")

   
def google_login(request):
    scope = "https://www.googleapis.com/auth/userinfo.email"
    client_id = getattr(settings, "SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    return redirect(
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}"
    )

def google_callback(request):
    client_id = getattr(settings, "SOCIAL_AUTH_GOOGLE_CLIENT_ID")
    client_secret = getattr(settings, "SOCIAL_AUTH_GOOGLE_SECRET")
    code = request.GET.get('code')

    token_req = requests.post(
        f"https://oauth2.googleapis.com/token?client_id={client_id}&client_secret={client_secret}&code={code}&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}&state={state}"
    )

    token_req_json = token_req.json()
    error = token_req_json.get("error")
    if error is not None:
        raise JSONDecodeError(error)
    access_token = token_req_json.get('access_token')

    email_req = requests.get(
        f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
    )
    email_req_status = email_req.status_code
    
    if email_req_status != 200:
        return JsonResponse(
            {'err_msg': 'failed to get email'},
            status=status.HTTP_400_BAD_REQUEST
        )
    email_req_json = email_req.json()
    email = email_req_json.get('email')
    print(email)
    try:
        print("email",email)
        user = User.objects.get(email=email)
        print("user",user)
        
        social_user = SocialAccount.objects.get(user=user)
        
        if social_user is None:
            return JsonResponse(
                {'err_msg': 'email exists but not social user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if social_user.provider != 'google':
            return JsonResponse(
                {'err_msg': 'no matching social type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = {'access_token': access_token, 'code': code}
        accept = requests.post(
            f"{BASE_URL}users/google/login/finish/", data=data
        )
        accept_status = accept.status_code
       
        if accept_status != 200:
            return JsonResponse(
                {'err_msg': 'failed to signin'},
                status=accept_status
            )
        accept_json = accept.json()
        accept_json.pop('user', None)

        return JsonResponse(accept_json)
    except User.DoesNotExist:

        data = {'access_token': access_token, 'code': code}
        
        accept = requests.post(
            f"{BASE_URL}users/google/login/finish/", data=data
        )
        accept_status = accept.status_code
       
        if accept_status != 200:
            return JsonResponse(
                {'err_msg': 'failed to signup'},
                status=accept_status
            )
        accept_json = accept.json()
        accept_json.pop('user', None)
        return JsonResponse(accept_json)

class GoogleLogin(SocialLoginView):
    adapter_class = google_view.GoogleOAuth2Adapter
    callback_url = GOOGLE_CALLBACK_URI
    client_class = OAuth2Client