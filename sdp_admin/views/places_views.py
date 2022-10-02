import io
import time
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.images import ImageFile
from django.http import HttpResponse, JsonResponse

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework import status
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework import mixins
from rest_framework import generics
from functools import partial

from places.models import SNSUrl, SNSType, PlacePhoto, Place
from places.serializers import PlacePhotoSerializer, SNSUrlSerializer, MapMarkerSerializer, PlaceSerializer, PlaceDetailSerializer 
from core.permissions import IsSdpStaff

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

    queryset = Place.objects.all().order_by('id')
    serializer_class = PlaceSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]
    pagination_class = PlacePagination

    @action(detail=False, methods=['post'])
    def photos(self, request):
        file_obj = request.FILES['file']
        ext = file_obj.name.split(".")[-1]

        if ext not in ["jpg", "png", "gif", "jpeg", ]:
            return JsonResponse({
                'status': 'error',
                'message': 'Wrong file format'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            caption = request.POST['caption']
            place_name = request.POST['place_name']

            file_path = '{}/{}.{}'.format(place_name,
                                        'target' + str(int(time.time())), ext)
            image = ImageFile(io.BytesIO(file_obj.read()), name=file_path)
            
            photo = PlacePhoto(caption=caption, image=image)
            photo.save()
        except:
            return JsonResponse({
                'status': 'error',
                'message': 'Unknown'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PlacePhotoSerializer(photo)
        print(serializer.data['image'])
        return JsonResponse({
            'status': 'success',
            'data': {'location': serializer.data['image']},
        }, status=status.HTTP_201_CREATED)

    def post(self, request):
        print("Hello")

        


class PlacePhotoViewSet(CreateAPIView):
    queryset = PlacePhoto.objects.all()
    serializer_class = PlacePhotoSerializer
