from places.serializers import PlaceSerializer,PlaceDetailSerializer, PlaceLikeSerializer
from users.serializers import UserSerializer
from .models import Place, Photo
from users.models import User

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action

import os
import json
import requests
import pandas as pd
import geopandas as gpd
#from tqdm import tqdm
import haversine as hs
from haversine import Unit

# Create your views here.

kakao_rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
#google_rest_api_key = getattr(settings, 'GOOGLE')

def addr_to_lat_lon(addr):
    url = 'https://dapi.kakao.com/v2/local/search/address.json?query={address}'.format(address=addr)
    headers = {"Authorization": "KakaoAK " + kakao_rest_api_key}
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
    page_size = 20
    page_size_query_param = 'page_size'

#def MyLocation()
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
        response = Response(PlaceDetailSerializer(place).data, status=status.HTTP_200_OK)
        return response
    
    

class PlaceLikeView(viewsets.ModelViewSet):
    serializer_class=PlaceLikeSerializer
    queryset = Place.objects.all()
    permission_classes=[
        IsAuthenticated,
    ]
    def get(self,request,pk):
        place = get_object_or_404(Place, pk=pk)
        like_id = place.place_likeuser_set.all()
        users = User.objects.filter(id__in=like_id)
        serializer = UserSerializer(users, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        access_token = request.META.get('HTTP_AUTHORIZATION')
        if not serializer.is_valid(raise_exception=True):
            return Response({"msg": "serializer is not valid"})

        place = get_object_or_404(Place, pk=serializer.validated_data['id'])
        if request.user.is_authenticated:
            user = request.user
            profile = User.objects.get(email=user)
            check_like = place.place_likeuser_set.filter(pk=profile.pk)

            if check_like.exists():
                place.place_likeuser_set.remove(profile)
                place.place_like_cnt -= 1
                place.save()
                return Response(status.HTTP_204_NO_CONTENT)
            else:
                place.place_likeuser_set.add(profile)
                place.place_like_cnt += 1
                place.save()
                return Response(status.HTTP_201_CREATED)
        else:
            return Response(status.HTTP_204_NO_CONTENT)
        