import json
import requests

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from silk.profiling.profiler import silk_profile
import pandas as pd
import boto3
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Place, PlacePhoto, SNSType, SNSUrl
from users.models import User
from places.serializers import PlaceSerializer,PlaceDetailSerializer, MapMarkerSerializer
from users.serializers import UserSerializer
from sasmproject.swagger import param_search,param_filter,param_id,PlaceLikeView_post_params
# Create your views here.
aws_access_key_id = getattr(settings,'AWS_ACCESS_KEY_ID')
aws_secret_access_key = getattr(settings,'AWS_SECRET_ACCESS_KEY')
kakao_rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')

class MapMarkerView(viewsets.ModelViewSet):
    '''
        map marker 표시를 위해 모든 장소를 주는 API
    '''
    queryset = Place.objects.all()
    serializer_class = MapMarkerSerializer
    permission_classes=[
        AllowAny,
    ]
    @swagger_auto_schema(operation_id='api_places_map_info_get',security=[])
    def get(self, request):
        serializer = MapMarkerSerializer(self.queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
class BasicPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

class PlaceListView(viewsets.ModelViewSet):
    '''
        place의 list의 정보를 주는 API
    '''
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes=[
        AllowAny,
    ]
    pagination_class=BasicPagination
    
    @swagger_auto_schema(operation_id='api_places_place_search_get',
                        manual_parameters=[param_search,param_filter],security=[])
    def get(self, request):
        '''
        search,filter를 적용한 장소 리스트를 distance로 정렬하여 반환
        '''
        qs = self.get_queryset()
        search = request.GET.get('search','')
        
        # search 및 filtering
        search_list = qs.filter(Q(place_name__icontains=search))
        array = request.query_params.getlist('filter[]', '배열')
        query = None 
        if array != '배열':
            for a in array: 
                if query is None: 
                    query = Q(category=a) 
                else: 
                    query = query | Q(category=a)
            place = search_list.filter(query)
            serializer = self.get_serializer(
                place,
                many=True,
                context={
                    "left":request.query_params.get("left"),
                    "right":request.query_params.get("right"),
                    "request":request
                }
            )
            
        else:
            serializer = self.get_serializer(
                search_list,
                many=True,
                context={
                    "left":request.query_params.get("left"),
                    "right":request.query_params.get("right"),
                    "request":request
                }
            )
        
        # 검색 결과를 바탕으로 거리순 정렬 후 pagination
        serializer_data = sorted(
            serializer.data, key=lambda k: float(k['distance']))
        page = self.paginate_queryset(serializer_data)
    
        if page is not None:
            serializer = self.get_paginated_response(page)
        else:
            serializer = self.get_serializer(page, many=True)
            
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
class PlaceDetailView(viewsets.ModelViewSet):
    '''
        place의 detail 정보를 주는 API
    '''
    queryset = Place.objects.all()
    serializer_class = PlaceDetailSerializer
    permission_classes=[
        AllowAny,
    ]
    @swagger_auto_schema(operation_id='api_places_place_detail_get',
                        manual_parameters=[param_id],security=[])
    @silk_profile(name='place_detail')
    def get(self,request):
        '''
            Place의 detail한 정보를 주는 api
        '''
        pk = request.GET.get('id', '')
        place = Place.objects.get(id=pk)
        return Response({
            'status': 'success',
            'data': PlaceDetailSerializer(place,context={'request': request}).data,
        }, status=status.HTTP_200_OK)

class PlaceLikeView(viewsets.ModelViewSet):
    serializer_class=PlaceSerializer
    queryset = Place.objects.all()
    permission_classes=[
        IsAuthenticated,
    ]

    @swagger_auto_schema(operation_id='api_places_place_like_user_get')
    def get(self,request,pk):
        '''
            장소의 좋아요한 유저 list를 반환하는 api
        '''
        place = get_object_or_404(Place, pk=pk)
        like_id = place.place_likeuser_set.all()
        users = User.objects.filter(id__in=like_id)
        serializer = UserSerializer(users, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
  
    @swagger_auto_schema(operation_id='api_places_place_like_post',
                        request_body=PlaceLikeView_post_params,
                        responses={200:'success'})
    def post(self, request):
        '''
            좋아요 및 좋아요 취소를 수행하는 api
        '''
        id = request.data['id']
        place = get_object_or_404(Place, pk=id)
        if request.user.is_authenticated:
            user = request.user
            profile = User.objects.get(email=user)
            check_like = place.place_likeuser_set.filter(pk=profile.pk)

            if check_like.exists():
                place.place_likeuser_set.remove(profile)
                place.place_like_cnt -= 1
                place.save()
                return Response({
                    "status" : "success",
                },status=status.HTTP_200_OK)
            else:
                place.place_likeuser_set.add(profile)
                place.place_like_cnt += 1
                place.save()
                return Response({
                    "status" : "success",
                },status=status.HTTP_200_OK)
        else:
            return Response({
            'status': 'fail',
            'data' : { "user" : "user is not authenticated"},
        }, status=status.HTTP_401_UNAUTHORIZED)

def get_s3(place,num):
    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)
        obj_list = s3.list_objects(Bucket='sasm-bucket',Prefix='media/places/{}'.format(place))
        content_list = obj_list['Contents']
        for content in content_list:
            if str(content['Key']).find('{}/'.format(place) + str(num) + '.') != -1:
                result = content['Key']
                break
        print(place)
        print(result)
        ext = result.split(".")[-1]
        return ext
    except Exception as e:
        print('에러',e)

def addr_to_lat_lon(addr):
    url = 'https://dapi.kakao.com/v2/local/search/address.json?query={address}'.format(address=addr)
    headers = {"Authorization": "KakaoAK " + kakao_rest_api_key}
    result = json.loads(str(requests.get(url, headers=headers).text))
    match_first = result['documents'][0]['address']
    x=float(match_first['x'])
    y=float(match_first['y'])
    return (x, y)

@swagger_auto_schema(operation_id='func_places_save_place_get', method='get',responses={200:'success'},security=[])
@api_view(['GET'])
def save_place_db(request):
    '''
        SASM_DB 엑셀파일을 읽어 Place,PlacePhoto,SNS를 DB에 저장하는 함수
    '''
    df = pd.read_excel("SASM_DB.xlsx", engine="openpyxl")
    df = df.fillna('')
    for dbfram in df.itertuples():
        place_name = dbfram[1]
        ext = get_s3(place_name, "rep")
        
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
            longitude=addr_to_lat_lon(dbfram[16])[0],
            latitude=addr_to_lat_lon(dbfram[16])[1],
            short_cur=dbfram[17],
            phone_num=dbfram[18],
            rep_pic = 'places/{}/rep.{}'.format(place_name, ext),
            )
        obj.save()
        id = obj.id
        for j in range(1,4):
            ext = get_s3(place_name, str(j))            
            img = PlacePhoto.objects.create(
                image = 'places/{}/{}.{}'.format(place_name, str(j), ext),
                place_id=id,
                )
            img.save()
        
        k = 19
        while(True):
            if(k<25 and len(dbfram[k])!=0):
                sns_type = dbfram[k]
                if SNSType.objects.filter(name=sns_type).exists():
                    obj1 = SNSUrl.objects.create(
                        snstype_id=SNSType.objects.get(name=sns_type).id,
                        url = dbfram[k+1],
                        place_id=id,
                    )
                    obj1.save()
                else:
                    obj2 = SNSType.objects.create(
                        name = sns_type,
                    )
                    obj2.save()
                    obj3 = SNSUrl.objects.create(
                        snstype_id=obj2.id,
                        url = dbfram[k+1],
                        place_id=id,
                    )
                    obj3.save()
                k+=2
            else:
                break
    return Response({'msg': 'success'})
