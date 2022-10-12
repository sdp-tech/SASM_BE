import io
from re import X
import time
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.images import ImageFile
from django.http import HttpResponse, JsonResponse

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action, api_view
from rest_framework import status
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework import mixins
from rest_framework import generics
from functools import partial

from places.models import SNSUrl, SNSType, PlacePhoto, Place, get_upload_path
from ..serializers.places_serializers import PlacesAdminSerializer, PlacePhotoAdminSerializer, SNSTypeSerializer, SNSUrlSerializer
from core.permissions import IsSdpStaff
from places.views import addr_to_lat_lon
from users import serializers, views

class SetPartialMixin:
    def get_serializer_class(self, *args, **kwargs):
        serializer_class = super().get_serializer_class(*args, **kwargs)
        return partial(serializer_class, partial=True)

class PlacePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

class PlaceViewSet(SetPartialMixin, viewsets.ModelViewSet):
    """
    모든 장소를 리스트, 또는 새로운 장소 생성
    장소 가져오기, 업데이트 또는 삭제
    """
    aws_access_key_id = getattr(settings,'AWS_ACCESS_KEY_ID')
    aws_secret_access_key = getattr(settings,'AWS_SECRET_ACCESS_KEY')
    kakao_rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')

    queryset = Place.objects.all().order_by('id')
    serializer_class = PlacesAdminSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]
    # pagination_class = PlacePagination

    @action(detail=False, methods=['post']) 
    def save_place(self, request):
        place_info = request.data
        addr = place_info['address']
        place_info['longitude'], place_info['latitude'] = addr_to_lat_lon(addr)
        #category 값이 null로 들어오는 경우
        category_array = ['vegan_category','tumblur_category','reusable_con_category','pet_category']
        for a in category_array:
            if(place_info[a]=='null'):
                place_info[a] = ""

        rep_pic = place_info['rep_pic']
        pic1, pic2, pic3 = place_info['placephoto1'], place_info['placephoto2'], place_info['placephoto3']
        pics = [pic1, pic2, pic3]
        
        del place_info['placephoto1']
        del place_info['placephoto2']
        del place_info['placephoto3']
        
        count = int(place_info['snscount'])
        sns = {}
        if(count >0):
            for i in range(count):
                snstype,url = place_info[i].split(',')
                sns[snstype] = url
                del place_info[i]

        serializer = PlacesAdminSerializer(data=place_info)
        if serializer.is_valid():
            created_place = serializer.save()
            """ sns """
            print(sns)
            for key,value in sns.items():
                try:
                    snstype = SNSType.objects.get(id=key)
                    snsurl = SNSUrl(url=value,place=created_place,snstype=snstype)
                    snsurl.save()
                except:
                    snstype = SNSType(name=key)
                    snstype.save()
                    created_snstype = SNSType.objects.get(name=key)
                    print('생성됐나',created_snstype)
                    snsurl = SNSUrl(url=value,place=created_place,snstype=created_snstype)
                    snsurl.save()
            """ pics """
            for pic in pics:
                ext = pic.name.split(".")[-1]

                if ext not in ["jpg", "png", "gif", "jpeg",]:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Wrong file format'
                    }, status=status.HTTP_400_BAD_REQUEST)

                try: 
                    file_path = '{}/{}.{}'.format(created_place.place_name,pics.index(pic)+1, ext)
                    image = ImageFile(io.BytesIO(pic.read()), name=file_path)
                    photo = PlacePhoto(image=image, place=created_place)
                    photo.save()

                except:
                    print()
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Unknown'
                    }, status=status.HTTP_400_BAD_REQUEST)

            return JsonResponse({
                'status': 'success',
                'data': serializer.data,
                }, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put']) 
    def update_place(self, request):
        place_info = request.data.copy()
        place_id = place_info['id']
        place = Place.objects.get(id=place_id)

        addr = place_info['address']
        place_info['longitude'], place_info['latitude'] = addr_to_lat_lon(addr)
        
        category_array = ['vegan_category','tumblur_category','reusable_con_category','pet_category']
        for a in category_array:
            if(place_info[a]=='null'):
                place_info[a] = ""
        pics = {}
        cnt = 0
        photo_array = ['placephoto1','placephoto2','placephoto3']
        for p in photo_array:
            if p in place_info:
                pics[cnt] = place_info[p]
                del place_info[p]
            cnt += 1
        #rep_pic이 변경되지 않았을 경우 serializer에서 삭제
        if type(place_info['rep_pic']) is str:
            del place_info['rep_pic']

        count = int(place_info['snscount'])
        sns = {}
        if(count >0):
            for i in range(count):
                snstype,url = place_info[i].split(',')
                sns[int(snstype)] = url
                del place_info[i]

        serializer = PlacesAdminSerializer(instance=place, data=place_info, partial=True)
        print(serializer)
        if serializer.is_valid():
            created_place = serializer.save()
            """ sns """
            # print(sns)
            # list = SNSUrl.objects.filter(place=created_place)
            # for l in list:
            #     if(l.snstype in sns):
            #         if(l.url == sns[l.id]):
                        

            # for key,value in sns.items():
            #     try:
            #         snstype = SNSType.objects.get(id=key)
            #         snsurl = SNSUrl(url=value,place=created_place,snstype=snstype)
            #         snsurl.save()
            #     except:
            #         snstype = SNSType(name=key)
            #         snstype.save()
            #         created_snstype = SNSType.objects.get(name=key)
            #         print('생성됐나',created_snstype)
            #         snsurl = SNSUrl(url=value,place=created_place,snstype=created_snstype)
            #         snsurl.save()
            photo_list = created_place.photos.all().order_by("id")
            print(photo_list)
            
            """ pics """
            if(len(pics) > 0):
                for key,value in pics.items():
                    ext = value.name.split(".")[-1]

                    if ext not in ["jpg", "png", "gif", "jpeg",]:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Wrong file format'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    try:
                        file_path = '{}/{}.{}'.format(created_place.place_name,key+1, ext)
                        image = ImageFile(io.BytesIO(value.read()), name=file_path)

                        photo_id = photo_list[key].id
                        print(photo_id)
                        photo = PlacePhoto.objects.get(id=photo_id)
                        photo.image = image

                        photo.save()
                    except:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Unknown'
                        }, status=status.HTTP_400_BAD_REQUEST)

            return JsonResponse({
                'status': 'success',
                'data': serializer.data,
                }, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)     

class PlacesPhotoViewSet(viewsets.ModelViewSet):
    """
    장소에 해당하는 PlacePhoto를 보내주는 api
    """
    queryset = PlacePhoto.objects.all()
    serializer_class = PlacePhotoAdminSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]

    def get(self,request,pk):
        photo = PlacePhoto.objects.filter(place_id=pk)
        return Response(self.get_serializer(photo,many=True).data)

class SNSTypeViewSet(viewsets.ModelViewSet):
    """
        db에 존재하는 SNS Type을 json으로 보내 주는 api
    """

    queryset = SNSType.objects.all()
    serializer_class = SNSTypeSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]

class SNSUrlViewSet(viewsets.ModelViewSet):
    """
        장소에 해당하는 url을 보내주는 api
    """

    queryset = SNSUrl.objects.all()
    serializer_class = SNSUrlSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]
    
    def get(self,request,pk):
        snsurl = SNSUrl.objects.filter(place_id=pk)
        return Response(self.get_serializer(snsurl,many=True).data)
    
