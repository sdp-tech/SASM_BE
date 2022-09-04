from webbrowser import get
from .models import Story
from users.models import User
from .serializers import StoryListSerializer, StoryDetailSerializer

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination

import datetime

# @login_required
# def story_like(request, id):
#     story = get_object_or_404(Story, id=id)
#     user = request.user
#     profile = User.objects.get(email=user)
#     check_like = story.story_likeuser_set.filter(id=profile.id)

#     if check_like.exists():
#         story.story_likeuser_set.remove(profile)
#         story.story_like_cnt -= 1
#         story.save()
#         return JsonResponse({'msg': 'cancel'})
#     else:
#         story.story_likeuser_set.add(profile)
#         story.story_like_cnt += 1
#         story.save()
#         return JsonResponse({'msg': 'click'})
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
                return Response(status.HTTP_204_NO_CONTENT)
            else:
                story.story_likeuser_set.add(profile)
                story.story_like_cnt += 1
                story.save()
                return Response(status.HTTP_201_CREATED)
        else:
            return Response(status.HTTP_204_NO_CONTENT)

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
        search_list = qs.filter(Q(title__icontains=search))
        page = self.paginate_queryset(search_list)
        if page is not None:
            serializer = self.get_paginated_response(self.get_serializer(page, many=True).data) 
        else:
            serializer = self.get_serializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        response = Response(serializer.data, status=status.HTTP_200_OK)
        print(response)

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
        response = Response(serializer.data, status=status.HTTP_200_OK)
        return response