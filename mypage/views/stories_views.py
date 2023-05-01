from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination


from users.selectors import UserStorySelector

from core.views import get_paginated_response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class UserStoryGetApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 6
        page_size_query_param = 'page_size'

    class UserStoryGetSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        place_name = serializers.SerializerMethodField()
        title = serializers.CharField()
        preview = serializers.CharField()
        rep_pic = serializers.ImageField()
        views = serializers.IntegerField()
        writer = serializers.CharField()
        created = serializers.DateTimeField()

        def get_place_name(self, obj):
            return obj.address.place_name

    @swagger_auto_schema(
        operation_id='작성한 스토리 조회',
        operation_description='''
                유저가 작성한 스토리를 조회합니다.<br/>
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "id": 1,
                        "place_name": "르타리",
                        "title": "버섯의 세계",
                        "preview": "눈과 입이 즐거운 곳",
                        "rep_pic": "https://abc.com/1.jpg",
                        "views": 10,
                        "writer": "sdptech@gmail.com",
                        "created": "2023-04-13"
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        selector = UserStorySelector(user=request.user)
        story_list = selector.list()

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.UserStoryGetSerializer,
            queryset=story_list,
            request=request,
            view=self
        )
