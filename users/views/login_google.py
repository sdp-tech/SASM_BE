from allauth.socialaccount.providers.google import views as google_view
from ..models import User
from .social_login import *
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

BASE_URL = 'https://api.sasm.co.kr/'
GOOGLE_CALLBACK_URI = 'https://www.sasm.co.kr/googleredirect/'

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def google_callback(request):
    access_token = request.data.get('accessToken')
    
    email_req = requests.get(
        f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
    )
    email_req_status = email_req.status_code
    
    if email_req_status != 200:
        return Response({
                        'status': 'error',
                        'message': 'failed to get email',
                        'code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
    email_req_json = email_req.json()
    email = email_req_json.get('email')
    nickname = email.split("@")[0]
    
    try:
        user = User.objects.get(email=email)    
        social_user = SocialAccount.objects.get(user=user)
        if social_user is None:
            return Response({
                        'status': 'error',
                        'message': 'Email exists but not social user',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
        
        if social_user.provider != 'google':
            return Response({
                        'status': 'error',
                        'message': 'Social type does not match',
                        'code': 404
                    }, status=status.HTTP_404_NOT_FOUND)
            
        data = {'access_token': access_token}
        accept = requests.post(
            f"{BASE_URL}users/google/login/finish/", data=data
        )
        accept_status = accept.status_code
        
        if accept_status != 200:
            return Response({
                        'status': 'error',
                        'message': 'Failed to signin',
                        'code': accept_status
                    }, status=accept_status)
        accept_json = accept.json()
        accept_json.pop('user', None)
        
        response = {
                'access': accept_json.get('access_token'),
                'refresh': accept_json.get('refresh_token'),
                'nickname' : nickname
            }
        return Response({
                    'status': 'success',
                    'data': response,
                }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        data = {'access_token': access_token}
        accept = requests.post(
            f"{BASE_URL}users/google/login/finish/", data=data
        )
        accept_status = accept.status_code
        
        if accept_status != 200:
            return Response({
                        'status': 'error',
                        'message': 'Failed to signup',
                        'code': accept_status
                    }, status=accept_status)
            
        user = User.objects.get(email=email)
        user.is_active = True
        user.nickname = nickname
        user.save()
            
        accept_json = accept.json()
        accept_json.pop('user', None)
        
        response = {
                'access': accept_json.get('access_token'),
                'refresh': accept_json.get('refresh_token'),
                'nickname' : nickname
            }
        return Response({
                    'status': 'success',
                    'data': response,
                }, status=status.HTTP_200_OK)

class GoogleLogin(SocialLoginView):
    adapter_class = google_view.GoogleOAuth2Adapter
    callback_url = GOOGLE_CALLBACK_URI
    client_class = OAuth2Client