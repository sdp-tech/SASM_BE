from allauth.socialaccount.providers.google import views as google_view
from ..models import User
from .social_login import *
# random state 생성하기
state = getattr(settings, 'STATE')
STATE_LENGTH = 15
string_pool = string.ascii_letters + string.digits
for i in range(STATE_LENGTH):
    state += random.choice(string_pool)

BASE_URL = 'http://127.0.0.1:8000/'
GOOGLE_CALLBACK_URI = BASE_URL + 'users/google/callback/'


# 구글 소셜 로그인
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

    try:
        user = User.objects.get(email=email)    
        if user is None:
            print("user")    
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