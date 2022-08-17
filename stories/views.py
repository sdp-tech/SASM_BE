from http.client import HTTPResponse
from .models import Story
from users.models import User
from .serializers import StorySerializer

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction

from rest_framework import generics
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly

import datetime

@login_required
def story_like(request, id):
    story = get_object_or_404(Story, id=id)
    user = request.user
    profile = User.objects.get(email=user)
    check_like = story.story_likeuser_set.filter(id=profile.id)

    if check_like.exists():
        story.story_likeuser_set.remove(profile)
        story.story_like_cnt -= 1
        story.save()
        return JsonResponse({'msg': 'cancel'})
    else:
        story.story_likeuser_set.add(profile)
        story.story_like_cnt += 1
        story.save()
        return JsonResponse({'msg': 'click'})

class StoryDetailView(generics.RetrieveAPIView):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def retrieve(self, request, id):
        detail_story = get_object_or_404(self.get_queryset(), id=id)

        # 쿠키 초기화할 시간. 당일 자정
        change_date = datetime.datetime.replace(timezone.datetime.now(), hour = 23, minute = 59, second = 0)
        # %a: locale 요일(단축 표기), %b: locale 월 (단축 표기), %d: 10진수 날짜, %Y: 10진수 4자리 년도
        # strftime: 서식 지정 날짜 형식 변경.
        expires = datetime.datetime.strftime(change_date, "%a, %d-%b-%Y %H:%M:%S GMT")
        print(expires)
        expire_date, now = timezone.datetime.now(), timezone.datetime.now()
        expire_date += datetime.timedelta(days=1)
        expire_date = expire_date.replace(hour=0, minute=0, second=0, microsecond=0)
        expire_date -= now
        max_age = expire_date.total_seconds()

        # response를 미리 받기
        serializer = self.get_serializer(detail_story)
        response = JsonResponse(serializer.data, status=status.HTTP_200_OK)
        print(response)

        # 쿠키 읽기, 생성하기

        if request.COOKIES.get('hit') is not None:
            cookies = request.COOKIES.get('hit')
            cookies_list = cookies.split('|')
            if str(id) not in cookies_list:
                response.set_cookie('hit', cookies+f'|{id}', max_age=max_age)
                with transaction.atomic():
                    detail_story.views += 1
                    detail_story.save()

        else:
            print('cookie 없음')
            print(id)
            response.set_cookie('hit', value=id, path='/',secure=False, max_age=max_age)
            print(request.COOKIES)
            detail_story.views += 1
            detail_story.save()

        serializer = self.get_serializer(detail_story)
        response = Response(serializer.data, status=status.HTTP_200_OK)
        return response