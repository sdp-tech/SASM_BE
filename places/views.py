from places.serializers import PlaceSerializer
from .models import Place, Photo
from users.models import User

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

import json
import requests
import pandas as pd

# Create your views here.

rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')

@login_required
def place_like(request, id):
    place = get_object_or_404(Place, id=id)
    user = request.user
    profile = User.objects.get(email=user)
    check_like = place.place_likeuser_set.filter(id=profile.id)

    if check_like.exists():
        place.place_likeuser_set.remove(profile)
        place.place_like_cnt -= 1
        place.save()
        return JsonResponse({'msg': 'cancel'})
    else:
        place.place_likeuser_set.add(profile)
        place.place_like_cnt += 1
        place.save()
        return JsonResponse({'msg': 'click'})

def addr_to_lat_lon(addr):
    url = 'https://dapi.kakao.com/v2/local/search/address.json?query={address}'.format(address=addr)
    headers = {"Authorization": "KakaoAK " + rest_api_key}
    result = json.loads(str(requests.get(url, headers=headers).text))
    match_first = result['documents'][0]['address']
    x=float(match_first['x'])
    y=float(match_first['y'])
    return (x, y)

def save_place_db(request):
    df = pd.read_excel("SASM_DB.xlsx", engine="openpyxl")
    df = df.fillna('')
    i=1
    for dbfram in df.itertuples():
        obj = Place.objects.create(
            place_name=dbfram[1],
            category=dbfram[2],
            vegan_category=dbfram[3],
            tumblur_category=dbfram[4],
            reusable_con_category=dbfram[5],
            pet_category=dbfram[6],
            mon_hours=dbfram[7],
            tues_hours=dbfram[8],
            wed_hours=dbfram[9],
            thurs_hours=dbfram[10],
            fri_hours=dbfram[11],
            sat_hours=dbfram[12],
            sun_hours=dbfram[13],
            etc_hours=dbfram[14],
            place_review=dbfram[15],
            address=dbfram[16],
            left_coordinate=addr_to_lat_lon(dbfram[16])[0],
            right_coordinate=addr_to_lat_lon(dbfram[16])[1],
            short_cur=dbfram[17],
            rep_pic = dbfram[18],
            )
        obj.save()
        num = 19
        for j in range(3):
            img = Photo.objects.create(
                image = dbfram[num],
                place_id=i,
                )
            num+=1
            img.save()
        i+=1
    return JsonResponse({'msg': 'success'})

class BasicPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

class PlaceDetailView(viewsets.ModelViewSet):
    '''
        place의 detail 정보를 주는 API
    '''
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes=[
        AllowAny,
    ]
    pagination_class=BasicPagination
    
    def list(self,request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_paginated_response(self.get_serializer(page, many=True).data) 
        else:
            serializer = self.get_serializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self,request,pk):
        place = Place.objects.get(id=pk)
        response = Response(PlaceSerializer(place).data, status=status.HTTP_200_OK)
        return response