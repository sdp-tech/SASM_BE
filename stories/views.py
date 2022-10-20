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
from .models import Story
from users.models import User
from .serializers import StoryListSerializer, StoryDetailSerializer
from places.serializers import MapMarkerSerializer

class StoryLikeView(viewsets.ModelViewSet):
    '''
    스토리에 대한 좋아요 정보를 가져오는 API
    '''
    queryset = Story.objects.all()
    serializer_class = StoryDetailSerializer
    permission_classes=[
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
        search = request.GET.get('search','')
        search_list = qs.filter(Q(title__icontains=search)|Q(address__place_name__icontains=search))
        array = request.query_params.getlist('filter[]', '배열')
        query = None
        if array != '배열':
            for a in array: 
                if query is None: 
                    query = Q(address__category=a) 
                else: 
                    query = query | Q(address__category=a)
            print(query)
            story = search_list.filter(query)
            page = self.paginate_queryset(story)
        else:
            page = self.paginate_queryset(search_list)
        if page is not None:
            serializer = self.get_paginated_response(self.get_serializer(page, many=True).data) 
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
    #get
    def retrieve(self, request):
        id = request.GET['id']
        detail_story = get_object_or_404(self.get_queryset(),pk=id)
        story = self.get_queryset().filter(pk=id)
        # 쿠키 초기화할 시간. 당일 자정
        change_date = datetime.datetime.replace(timezone.datetime.now(), hour=23, minute=59, second=0)
        # %a: locale 요일(단축 표기), %b: locale 월 (단축 표기), %d: 10진수 날짜, %Y: 10진수 4자리 년도
        # strftime: 서식 지정 날짜 형식 변경.
        expires = datetime.datetime.strftime(change_date, "%a, %d-%b-%Y %H:%M:%S GMT")

        # response를 미리 받기
        serializer = self.get_serializer(story, many=True, context={'request': request})
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

        serializer = self.get_serializer(story, many=True, context={'request': request})
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