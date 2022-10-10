import io
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
from ..serializers.places_serializers import PlacesAdminSerializer, PlacePhotoAdminSerializer
from core.permissions import IsSdpStaff
from places.views import addr_to_lat_lon
from users import serializers, views
from sdp_admin.serializers.places_serializers import SNSTypeSerializer

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
    pagination_class = PlacePagination

    @action(detail=False, methods=['post']) 
    def save_place(self, request):
        place_info = request.data

        addr = place_info['address']
        place_info['longitude'], place_info['latitude'] = addr_to_lat_lon(addr)
        
        rep_pic = place_info['rep_pic']
        pic1, pic2, pic3 = place_info['pic1'], place_info['pic2'], place_info['pic3']
        pics = [pic1, pic2, pic3]

        del place_info['pic1']
        del place_info['pic2']
        del place_info['pic3']

        serializer = PlacesAdminSerializer(data=place_info)
        if serializer.is_valid():
            created_place = serializer.save()

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
        place_info = request.data
        place_id = place_info['id']
        place = Place.objects.get(id=place_id)

        addr = place_info['address']
        place_info['longitude'], place_info['latitude'] = addr_to_lat_lon(addr)
        
        rep_pic = place_info['rep_pic']
        pic1, pic2, pic3 = place_info['pic1'], place_info['pic2'], place_info['pic3']
        pics = [pic1, pic2, pic3]

        del place_info['pic1']
        del place_info['pic2']
        del place_info['pic3']

        serializer = PlacesAdminSerializer(instance=place, data=place_info)
        if serializer.is_valid():
            created_place = serializer.save()
            photo_list = created_place.photos.all().order_by("id")
            print(photo_list)
            
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

                    photo_id = photo_list[pics.index(pic)].id
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




class PlacesPhotoViewSet(CreateAPIView):
    queryset = PlacePhoto.objects.all()
    serializer_class = PlacePhotoAdminSerializer

class SNSTypeViewSet(viewsets.ModelViewSet):
    """
        db에 존재하는 SNS Type을 json으로 보내 주는 api
    """

    queryset = SNSType.objects.all().order_by('id')
    serializer_class = SNSTypeSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]
    
    def get(self, request):
        qs = self.get_queryset().order_by('id')
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
            
    
