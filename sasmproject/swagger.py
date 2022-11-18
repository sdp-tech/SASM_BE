from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
SAMPLE_RESP = {
    "201": openapi.Response(
        description="Returns status of Prediction ID",
        examples={
            "application/json": {
                "status": "success"
            }
        }
    ),
    "400": openapi.Response(
        description="Unauthorized to view the result",
        examples={
            "application/json": {
                "status": "error",
                "message": "invalid data",
                "code": 400,
            }
        }
    ),
}
OVERLAP_RESP = {
    "200": openapi.Response(
        description="success",
        examples={
            "application/json": {
                "status": "success",
                "data": {"overlap": "true"}
            }
        }
    ),
    "400": openapi.Response(
        description="Unknown error",
        examples={
            "application/json": {
                "status": "error",
                "message": "Unknown",
                "code": 400,
            }
        }
    ),
}
# parameter값 정의
param_search = openapi.Parameter('search', in_=openapi.IN_QUERY, description='유저가 입력한 검색 값',
                                 type=openapi.TYPE_STRING, required=False)
param_filter = openapi.Parameter('filter', in_=openapi.IN_QUERY, description='유저가 선택한 필터링 값',
                                 type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), required=False)
param_id = openapi.Parameter('id', in_=openapi.IN_QUERY, description='장소의 id',
                             type=openapi.TYPE_INTEGER, required=True)
param_place_name = openapi.Parameter('place_name', in_=openapi.IN_QUERY, description='장소의 이름',
                                     type=openapi.TYPE_STRING, required=True)
param_pk = openapi.Parameter('pk', in_=openapi.IN_PATH, description='object의 pk값',
                             type=openapi.TYPE_INTEGER, required=True)
PlaceLikeView_post_params = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='장소의 id값'),
    }
)
StoryViewSet_post_params = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'file': openapi.Schema(type=openapi.TYPE_FILE, description='Story Photo'),
    }
)
StoryCommentViewSet_list_params = openapi.Parameter('story', in_=openapi.IN_QUERY, description='스토리의 id',
                                                    type=openapi.TYPE_INTEGER, required=True)
