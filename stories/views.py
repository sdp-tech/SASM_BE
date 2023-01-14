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
from core.permissions import IsStoryCommentWriterOrReadOnly
from sasmproject.swagger import StoryCommentViewSet_list_params, param_id
from drf_yasg.utils import swagger_auto_schema


class StoryLikeView(viewsets.ModelViewSet):
    '''
    스토리에 대한 좋아요 정보를 가져오는 API
    '''
    queryset = Story.objects.all()
    serializer_class = StoryDetailSerializer
    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):
        id = request.data['id']
        story = get_object_or_404(Story, pk=id)
        if request.user.is_authenticated:
            user = request.user
            profile = User.objects.get(email=user)
            check_like = story.story_likeuser_set.filter(pk=profile.pk)

            if check_like.exists():
                story.story_likeuser_set.remove(profile)
                story.story_like_cnt -= 1
                story.save()
                return Response({
                    'status': 'success',
                }, status=status.HTTP_201_CREATED)
            else:
                story.story_likeuser_set.add(profile)
                story.story_like_cnt += 1
                story.save()
                return Response({
                    'status': 'success',
                }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 'success',
            }, status=status.HTTP_401_UNAUTHORIZED)


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

    def get(self, request):
        qs = self.get_queryset()
        search = request.GET.get('search', '')
        order_condition = request.GET.get('order', 'true')
        search_list = qs.filter(Q(title__icontains=search) | Q(
            address__place_name__icontains=search))
        # if len(array) > 0:
        #     for a in array:
        #         if query is None:
        #             query = Q(address__category=a)
        #         else:
        #             query = query | Q(address__category=a)
        #     story = search_list.filter(query)
        #     page = self.paginate_queryset(story)

        # else:
        #     page = self.paginate_queryset(search_list)
        if order_condition == 'true': #최신순
            queryset = search_list.order_by('-created')
        if order_condition == 'false' : #오래된 순
            queryset = search_list.order_by('created')
        queryset = self.paginate_queryset(queryset)
        if queryset is not None:
            serializer = self.get_paginated_response(
                self.get_serializer(queryset, many=True).data)
        else:
            serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)       

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
        IsStoryCommentWriterOrReadOnly,
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
