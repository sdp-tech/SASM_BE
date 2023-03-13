from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.serializers import ValidationError
from places.serializers import MapMarkerSerializer
from stories.mixins import ApiAuthMixin
from stories.selectors import StorySelector, semi_category
from stories.services import StoryCoordinatorService
from core.views import get_paginated_response
from .models import Story, StoryComment
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

import datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import ValidationError

from .models import Story, StoryComment
from users.models import User
from .serializers import StoryListSerializer, StoryDetailSerializer, StoryCommentSerializer, StoryCommentCreateSerializer, StoryCommentUpdateSerializer
from places.serializers import MapMarkerSerializer
from core.permissions import CommentWriterOrReadOnly
from sasmproject.swagger import StoryCommentViewSet_list_params, param_id


class StoryListApi(APIView):
    class Pagination(PageNumberPagination):
        page_size = 4
        page_size_query_param = 'page_size'

    class StoryListFilterSerializer(serializers.Serializer):
        search = serializers.CharField(required=False)
        latest = serializers.BooleanField(required=False)

    class StoryListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        title = serializers.CharField()
        preview = serializers.CharField()
        rep_pic = serializers.ImageField()
        views = serializers.IntegerField()
        story_like = serializers.BooleanField()
        place_name = serializers.CharField()
        category = serializers.CharField()
        semi_category = serializers.SerializerMethodField()

        def get_semi_category(self, obj):
            result = semi_category(obj.id)
            return result
        
    @swagger_auto_schema(
        operation_id='스토리 리스트',
        operation_description='''
            전달된 쿼리 파라미터에 부합하는 게시글 리스트를 반환합니다.<br/>
            <br/>
            search : 제목 혹은 장소 검색어<br/>
            latest : 최신순 정렬 여부 (ex: true)</br>
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
        filters_serializer.is_valid(raise_exception=True)
        filters = filters_serializer.validated_data
        story = StorySelector.list(
            search=filters.get('search', ''),
            latest=filters.get('latest', True),
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.StoryListOutputSerializer,
            queryset=story,
            request=request,
            view=self
        )
    
    
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
            service = StoryCoordinatorService(
                user = request.user
            )
            story_like = service.like_or_dislike(
                story_id=request.data['id'],
            )
        except:
            return Response({
                'status': 'fail',
                'message': '권한이 없거나 story가 존재하지 않습니다.',
            }, status=status.HTTP_401_UNAUTHORIZED)
        return Response({
            'status': 'success',
                'data': {'story_like': story_like},
            }, status=status.HTTP_201_CREATED)
    

class BasicPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'

class StoryListView(viewsets.ModelViewSet):
    '''
        Story의 list 정보를 주는 API
    '''
    queryset = Story.objects.all()
    serializer_class = StoryListSerializer
    permission_classes = [
        AllowAny,
    ]
    pagination_class = BasicPagination

    @swagger_auto_schema(operation_id='api_stories_recommend_story_get', manual_parameters=[param_id])
    def recommend_story(self, request):
        id = request.GET.get('id', '')
        qs = self.get_queryset()
        story = Story.objects.get(id=id)
        # story의 category와 같은 스토리 return
        qs = qs.filter(address__category=story.address.category).exclude(id=id)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_paginated_response(
                self.get_serializer(page, many=True).data
            )
        else:
            serializer = self.get_serializer(page, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class StoryDetailView(generics.RetrieveAPIView):
    '''
    조회수 중복 방지 - 쿠키 사용
    '''
    queryset = Story.objects.all()
    serializer_class = StoryDetailSerializer
    permission_classes = [AllowAny]
    # get

    def retrieve(self, request):
        id = request.GET['id']
        detail_story = get_object_or_404(self.get_queryset(), pk=id)
        story = self.get_queryset().filter(pk=id)
        # 쿠키 초기화할 시간. 당일 자정
        change_date = datetime.datetime.replace(
            timezone.datetime.now(), hour=23, minute=59, second=0)
        # %a: locale 요일(단축 표기), %b: locale 월 (단축 표기), %d: 10진수 날짜, %Y: 10진수 4자리 년도
        # strftime: 서식 지정 날짜 형식 변경.
        expires = datetime.datetime.strftime(
            change_date, "%a, %d-%b-%Y %H:%M:%S GMT")

        # response를 미리 받기
        serializer = self.get_serializer(
            story, many=True, context={'request': request})
        response = Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

        # 쿠키 읽기, 생성하기
        if request.COOKIES.get('hit') is not None:
            cookies = request.COOKIES.get('hit')
            cookies_list = cookies.split('|')
            if str(id) not in cookies_list:
                response.set_cookie('hit', cookies+f'|{id}', expires=expires)
                detail_story.views += 1
                detail_story.save()
                return response
        else:
            response.set_cookie(key='hit', value=id, expires=expires)
            detail_story.views += 1
            detail_story.save()
            return response

        serializer = self.get_serializer(
            story, many=True, context={'request': request})
        response = Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
        return response


class GoToMapView(viewsets.ModelViewSet):
    '''
        Map으로 연결하는 API
    '''
    queryset = Story.objects.all()
    serializer_class = MapMarkerSerializer
    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        story_id = request.GET['id']
        story = self.queryset.get(id=story_id)
        place = story.address
        serializer = self.get_serializer(place)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)


class StoryCommentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


class StoryCommentView(viewsets.ModelViewSet):
    '''
        Story 하위 comment 관련 작업 API
    '''
    queryset = StoryComment.objects.all().order_by('id')
    serializer_class = StoryCommentSerializer
    permission_classes = [
        CommentWriterOrReadOnly,
    ]
    pagination_class = StoryCommentPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return StoryCommentCreateSerializer
        elif self.action == 'update':
            return StoryCommentUpdateSerializer
        return StoryCommentSerializer  # read op, destroy op

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @swagger_auto_schema(operation_id='api_stories_comments_get')
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'status': 'success',
            'data': response.data,
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_stories_comments_list', manual_parameters=[StoryCommentViewSet_list_params])
    def list(self, request, *args, **kwargs):
        '''특정 스토리 하위 댓글 조회'''

        story_id = request.GET.get('story')

        serializer = self.get_serializer(
            StoryComment.objects.filter(story=story_id),
            many=True,
            context={
                "story": Story.objects.get(id=story_id),
            }
        )
        # 댓글, 대댓글별 pagination 따로 사용하는 대신, 댓글 group(parent+childs)별로 정렬
        # 댓글의 경우 id값을, 대댓글의 경우 parent(상위 댓글의 id)값을 대표값으로 설정해 정렬(tuple의 1번째 값)
        # 댓글 group 내에서는 id 값을 기준으로 정렬(tuple의 2번째 값)
        serializer_data = sorted(
            serializer.data, key=lambda k: (k['parent'], k['id']) if k['parent'] else (k['id'], k['id']))
        page = self.paginate_queryset(serializer_data)

        if page is not None:
            serializer = self.get_paginated_response(page)
        else:
            serializer = self.get_serializer(page, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_stories_comments_post')
    def create(self, request, *args, **kwargs):
        try:
            super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response({
                'status': 'fail',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'fail',
                'message': 'unknown',
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_stories_comments_patch')
    def update(self, request, *args, **kwargs):
        try:
            # partial update
            kwargs['partial'] = True
            super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response({
                'status': 'fail',
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'fail',
                'message': 'unknown',
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_stories_comments_delete')
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            'status': 'success',
        }, status=status.HTTP_200_OK)