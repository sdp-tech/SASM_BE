from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from allauth.socialaccount.providers.kakao import views as kakao_view
from ..models import User
from .social_login import *

BASE_URL = 'http://127.0.0.1:8000/'
KAKAO_CALLBACK_URI = BASE_URL + 'users/kakao/callback/'

# 카카오 소셜 로그인 - 코드 요청
@method_decorator(csrf_exempt)
def kakao_login(request):
    rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={rest_api_key}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code"
    )

# 카카오 소셜 로그인 - 토큰 요청
@method_decorator(csrf_exempt)
def kakao_callback(request):
    rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
    code = request.GET.get("code")
    redirect_uri = KAKAO_CALLBACK_URI
    
    token_req = requests.get(
        f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={rest_api_key}&redirect_uri={redirect_uri}&code={code}"
    )
    token_req_json = token_req.json()
    error = token_req_json.get("error")
    if error is not None:
        raise JSONDecodeError(error)
    access_token = token_req_json.get("access_token")

    profile_request = requests.get('https://kapi.kakao.com/v2/user/me', headers={"Authorization": f'Bearer ${access_token}'})

    profile_json = profile_request.json()

    kakao_account = profile_json.get('kakao_account')

    # 이메일 외에도 프로필 이미지, 배경 이미지 url 등 가져올 수 있음
    
    email = kakao_account.get('email', None)

    try:
        user = User.objects.get(email=email)
        social_user = SocialAccount.objects.get(user=user)
        if social_user is None:
            return JsonResponse(
                {'err_msg': 'email exists but not social user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if social_user.provider != 'kakao':
            return JsonResponse(
                {'err_msg': 'no matching social type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = {'access_token': access_token, 'code': code}
        accept = requests.post(
            f"{BASE_URL}users/kakao/login/finish", data=data
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
            f"{BASE_URL}users/kakao/login/finish/", data=data
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

@method_decorator(csrf_exempt, name='dispatch')
class KakaoLogin(SocialLoginView):
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = KAKAO_CALLBACK_URI