#exception handling
from rest_framework.views import exception_handler
from rest_framework.response import Response
STATUS_RSP_INTERNAL_ERROR = {
    "status":"error",
    "code": "internal-error",
    "lang_message": {
        "ko": "알 수 없는 오류.",
        "en": "unknown error occurred.",
    }
}
def custom_exception_handler(exc,context):
    response = exception_handler(exc,context)
    if response is not None:
        response.data['status'] = 'error'
        response.data['message'] = response.data['detail']
        response.data['code'] = response.status_code
        del response.data['detail']
        return response
    else:
        STATUS_RSP_INTERNAL_ERROR['message'] = str(exc)
        STATUS_RSP_INTERNAL_ERROR['code'] = 500
        STATUS_RSP_INTERNAL_ERROR.pop('lang_message', None)
        return Response(STATUS_RSP_INTERNAL_ERROR, status=200)

