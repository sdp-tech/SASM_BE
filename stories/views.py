from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
from stories.selectors import StoryCoordinatorSelector, StoryCommentSelector, MapMarkerSelector, semi_category, StoryLikeSelector
from stories.services import StoryCoordinatorService, StoryCommentCoordinatorService
from core.views import get_paginated_response

from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class StoryLikeApi(APIView, ApiAuthMixin):

    @swagger_auto_schema(
        operation_id='스토리 좋아요 또는 좋아요 취소',
        operation_description='''
            전달된 id를 가지는 스토리글에 대한 사용자의 좋아요/좋아요 취소를 수행합니다.<br/>
            결과로 좋아요 상태(TRUE:좋아요, FALSE:좋아요X)가 반환됩니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"story_like": True}
                    }
                }
            ),
            "401": openapi.Response(
                description="Bad Request",    
            ),
        },
    )
    
    def post(self, request):
        try:
            print('11')
            service = StoryCoordinatorService(
                user = request.user
            )
            print('22', service)
            story_like = service.like_or_dislike(
                story_id=request.data['id'],
            )
            print('33', story_like)

            return Response({
                'status': 'success',
                'data': {'story_like': story_like},
            }, status=status.HTTP_201_CREATED)
        except ValidationError:
            return Response({
                'status': 'fail',
            }, status=status.HTTP_401_UNAUTHORIZED)

# def get_paginated_response(*, pagination_class, serializer_class, queryset, request, view):
#     paginator = pagination_class()

#     page = paginator.paginate_queryset(queryset, request, view=view)

#     if page is not None:
#         serializer = serializer_class(page, many=True)
#     else:
#         serializer = serializer_class(queryset, many=True)

#     return Response({
#         'status': 'success',
#         'data': paginator.get_paginated_response(serializer.data).data,
#     }, status=status.HTTP_200_OK)


class StoryListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class StoryListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        order_condition = serializers.CharField(required=False)

    class StoryListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        preview = serializers.CharField()
        rep_pic = serializers.ImageField()
        views = serializers.IntegerField()
        story_like = serializers.CharField()
        
        place_name = serializers.CharField()
        category = serializers.CharField()
        semi_category = serializers.SerializerMethodField()

        # def get_story_like(self, obj):
        #     return 'ok'

        def get_semi_category(self, obj):
            result = semi_category(obj.id)
            return result

       
    @swagger_auto_schema(
        operation_id='스토리 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 게시글 리스트를 반환합니다.<br/>
            <br/>
            search : 제목 혹은 장소 검색어<br/>
            order_condition : 최신순 정렬 여부 (ex: true)</br>
        ''',
        query_serializer=StoryListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'category': '녹색 공간',
                        'semi_category': '반려동물 출입 가능, 오보',
                        'preview': '서울숲. 가장 도시적인 단어...(최대 150자)',
                        'rep_pic': 'https://abc.com/1.jpg',
                        'story_like': True,
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.StoryListFilterSerializer(
            data=request.query_params)
        print('123', filters_serializer)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data
        print('filters', filters)

        selector = StoryCoordinatorSelector(
            user = request.user
        )
        story = selector.list(
            search=filters.get('search', ''),
            order_condition=filters.get('order', 'true'),
        )
        print('story', story)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.StoryListOutputSerializer,
            queryset=story,
            request=request,
            view=self
        )


class StoryRecommendApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class StoryRecommendListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        created = serializers.DateTimeField()

    @swagger_auto_schema(
        operation_id='story의 category와 같은 스토리 추천 리스트',
        operation_description='''
            해당 스토리의 category와 같은 스토리 리스트를 반환합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        selector = StoryCoordinatorSelector(
            user = request.user
        )

        recommend_story = selector.recommend_list(
            story_id = request.data['id']
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.StoryRecommendListOutputSerializer,
            queryset=recommend_story,
            request=request,
            view=self
        )


class StoryDetailApi(APIView):
    class StoryDetailOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        story_review = serializers.CharField()
        tag = serializers.CharField()
        html_content = serializers.CharField()
        story_like = serializers.CharField()  #결과가 'ok'또는 'none'으로 나오기 위함
        views = serializers.IntegerField()
        
        place_name = serializers.CharField()
        category = serializers.CharField()
        semi_category = serializers.CharField()

    # def get_semi_category(self, obj):
    #     result = semi_category(obj.id)
    #     return result

    @swagger_auto_schema(
        operation_id='스토리 글 조회',
        operation_description='''
            전달된 id에 해당하는 스토리 디테일을 조회합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'place_name': '서울숲',
                        'title': '도심 속 모두에게 열려있는 쉼터, 서울숲',
                        'category': '녹색 공간',
                        'semi_category': '반려동물 출입 가능, 텀블러 사용 가능, 비건',
                        'tag': '#생명 다양성 #자연 친화 #함께 즐기는',
                        'story_review': '"모두에게 열려있는 도심 속 가장 자연 친화적인 여가공간"',
                        'html_content': '서울숲. 가장 도시적인 단어...(최대 150자)',

                        'views': 45,
                        'story_like': 'ok',
                    },
                }
            ),
            "400":  openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        selector = StoryCoordinatorSelector(
            user=request.user
        )
        story = selector.detail(
            story_id=request.data['id'])
        print('detail: ', story)
        serializer = self.StoryDetailOutputSerializer(story)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


# class StoryPhotoApi(APIView):
#     class StoryPhotoOutputSerializer(serializers.Serializer):
#         caption = serializers.CharField()
#         image = serializers.ImageField(use_url=True)

#     @swagger_auto_schema(
#         operation_id='스토리 사진 조회',
#         operation_description='''
#             전달된 id에 해당하는 스토리 사진을 조회합니다.<br/>
#         ''',
#         responses={
#             "200": openapi.Response
#         }
#     )


class StoryCommentListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 20
        page_size_query_param = 'page_size'

    class StoryCommentListFilterSerializer(serializers.Serializer):
        story = serializers.IntegerField(required=True)

    class StoryCommentListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        story = serializers.IntegerField()
        content = serializers.CharField()
        isParent = serializers.BooleanField()
        group = serializers.CharField()
        nickname = serializers.CharField()
        email = serializers.CharField()
        mention = serializers.CharField()
        # mentionNickname = serializers.CharField()
        profile_image = serializers.ImageField()
        created_at = serializers.DateTimeField()
        updated_at = serializers.DateTimeField()

    @swagger_auto_schema(
        operation_id='스토리 댓글 조회',
        operation_description='''
            해당 story의 하위 댓글을 조회합니다.<br/>
        ''',
        query_serializer=StoryCommentListFilterSerializer,
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'content': '멋져요',
                        'isParent': True,
                        'group': 1,
                        'nickname': 'sdpygl',
                        'email': 'sdpygl@gmail.com',
                        'mention': 'sasm@gmail.com',
                        'profile_image': 'https://abc.com/1.jpg',
                        'created_at': '2019-08-24T14:15:22Z',
                        'updated_at': '2019-08-24T14:15:22Z',
                    }
                },
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        filters_serializer = self.StoryCommentListFilterSerializer(
            data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data

        selector = StoryCommentSelector()

        story_comments = selector.list(
            story_id=filters.get('story')  #story id값 받아서 넣기
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.StoryCommentListOutputSerializer,
            queryset=story_comments,
            request=request,
            view=self,
        )

    
class StoryCommentCreateApi(APIView, ApiAuthMixin):
    class StoryCommentCreateInputSerializer(serializers.Serializer):
        story=serializers.IntegerField()
        content = serializers.CharField()
        isParent = serializers.BooleanField()
        parent = serializers.IntegerField(required=False)
        mention = serializers.CharField(required=False)

        class Meta:
            examples = {
                'id': 1,
                'story': 1,
                'content': '정보 부탁드려요.',
                'isParent': True,
                'parent': 1,
                'mentionEmail': 'sdpygl@gmail.com',
            }

        def validate(self, obj):
            return StoryCommentCoordinatorService.validate(data=obj)

    @swagger_auto_schema(
        request_body=StoryCommentCreateInputSerializer,
        security=[],
        operation_id='스토리 댓글 생성',
        operation_description='''
            전달된 필드를 기반으로 해당 스토리의 댓글을 생성합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"id": 1}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),        
        },    
    )
    def post(self, request):
        serializer = self.StoryCommentCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = StoryCommentCoordinatorService(
            user=request.user
        )

        story_comment = service.create(
            story_id=data.get('story'),
            content=data.get('content'),
            isParent=data.get('isParent'),
            parent_id=data.get('parent', None),
            mentioned_email=data.get('mention', '')
        )

        # except ValidationError as e:
        #     return Response({
        #         'status': 'fail',
        #         'message': str(e),
        #     }, status=status.HTTP_400_BAD_REQUEST)
        # except Exception as e:
        #     return Response({
        #         'status': 'fail',
        #         'message': 'unknown',
        #     }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'data': {'id': story_comment.id},
        }, status=status.HTTP_200_OK)


class StoryCommentUpdateApi(APIView, ApiAuthMixin):
    class StoryCommnetUpdateInputSerializer(serializers.Serializer):
        content = serializers.CharField()
        mentionEmail = serializers.CharField(required=False)

        class Meta:
            examples = {
                'content': '저도요!!',
                'mentionEmail': 'sdppp@gamil.com',
            }

    @swagger_auto_schema(
        request_body=StoryCommnetUpdateInputSerializer,
        security=[],
        operation_id='스토리 댓글 수정',
        operation_description='''
            전달된 id에 해당하는 댓글을 업데이트합니다.<br/>
            전송된 모든 필드 값을 그대로 댓글에 업데이트하므로, 댓글에 포함되어야 하는 모든 필드 값이 request body에 포함되어야합니다.<br/>
            즉, 값이 수정된 필드뿐만 아니라 값이 그대로 유지되어야하는 필드도 함께 전송되어야합니다.<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"id": 1}
                    }
                },
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def patch(self, request, story_comment_id):
        story_comment = StoryComment.objects.get(id=story_comment_id)

        serializers = self.StoryCommnetUpdateInputSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)
        data = serializers.validated_data

        service = StoryCommentCoordinatorService(
            user=request.user
        )

        story_comment = service.update(
            story_comment_id=story_comment_id,
            content=data.get('content'),
            mentioned_email=data.get('mentionEmail', ''),
        )

        return Response({
            'status': 'success',
            'data': {'id': story_comment.id},
        }, status=status.HTTP_200_OK)


class StoryCommentDeleteApi(APIView, ApiAuthMixin):

    @swagger_auto_schema(
        operation_id='스토리 댓글 삭제',
        operation_description='''
            전달받은 id에 해당하는 댓글을 삭제합니다<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",     
            ),
            "400": openapi.Response(
                description="Bad Request",
            )        
        },
    )
    def delete(self, request, story_comment_id):
        
        service = StoryCommentCoordinatorService(
            user=request.user
        )

        service.delete(
            story_comment_id=story_comment_id
        )

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)


class GoToMapApi(APIView):

    @swagger_auto_schema(
        operation_id='스토리의 해당 장소로 Map 연결',
        operation_description='''
            전달받은 id에 해당하는 스토리의 장소로 Map을 연결해준다<br/>
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        selector = MapMarkerSelector(user=request.user)
        print('selector', selector)
        place = selector.map(story_id=request.data['id'])
        serializer = MapMarkerSerializer(place)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
