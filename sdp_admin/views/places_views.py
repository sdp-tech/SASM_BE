import io
from re import X
from functools import partial
from django.conf import settings
from django.core.files.images import ImageFile
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from places.models import SNSUrl, SNSType, PlacePhoto, Place
from ..serializers.places_serializers import PlacesAdminSerializer, PlacePhotoAdminSerializer, SNSTypeAdminSerializer, SNSUrlAdminSerializer
from core.permissions import IsSdpStaff
from places.views.save_place_excel import addr_to_lat_lon
from sasmproject.swagger import SAMPLE_RESP, param_place_name, param_pk, OVERLAP_RESP

class SetPartialMixin:
    def get_serializer_class(self, *args, **kwargs):
        serializer_class = super().get_serializer_class(*args, **kwargs)
        return partial(serializer_class, partial=True)

class PlaceViewSet(SetPartialMixin, viewsets.ModelViewSet):

    aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID')
    aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY')
    kakao_rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')

    queryset = Place.objects.all().order_by('id')
    serializer_class = PlacesAdminSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]

    @swagger_auto_schema(operation_id='api_sdp_admin_places_get')
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'status': 'Success',
            'data': response.data,
            },status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_sdp_admin_places_get')
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'status': 'Success',
            'data': response.data,
            },status=status.HTTP_200_OK)
            
    @swagger_auto_schema(operation_id='api_sdp_admin_places_save_place_post',request_body=PlacesAdminSerializer,
                        responses=SAMPLE_RESP)
    @action(detail=False, methods=['post'])
    def save_place(self, request):
        """
            장소 생성
        """
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
        
        # sns info 받기
        count = int(place_info['snscount'])
        sns = {}
        if(count >0):
            for i in range(count):
                snstype, snstype_name, url = place_info[str(i)].split(',')
                sns[snstype] = [snstype_name, url]
                del place_info[str(i)]

        serializer = PlacesAdminSerializer(data=place_info)
        if serializer.is_valid():
            created_place = serializer.save()
            
            """ sns """
            for key,value in sns.items():
                try:
                    snstype = SNSType.objects.get(id=key)
                    snsurl = SNSUrl(url=value[1], place=created_place, snstype=snstype)
                    snsurl.save()
                except:
                    snstype = SNSType(name=value[0])
                    snstype.save()
                    created_snstype = SNSType.objects.get(name=value[0])
                    snsurl = SNSUrl(url=value[1], place=created_place, snstype=created_snstype)
                    snsurl.save()
                    
            """ pics """
            for pic in pics:
                ext = pic.name.split(".")[-1]

                if ext not in ["jpg", "png", "gif", "jpeg", ]:
                    return Response({
                        'status': 'fail',
                        'data': 'Wrong file format',
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    file_path = '{}/{}.{}'.format(
                        created_place.place_name, pics.index(pic)+1, ext)
                    image = ImageFile(io.BytesIO(pic.read()), name=file_path)
                    photo = PlacePhoto(image=image, place=created_place)
                    photo.save()

                except:
                    return Response({
                        'status': 'error',
                        'message': 'Unknown',
                        'code' : 400,
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 'success',
            }, status=status.HTTP_201_CREATED)

        else:
            return Response({
                'status' : 'fail',
                'data' : serializer.errors,
            },status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_id='api_sdp_admin_places_update_place_put',request_body=PlacesAdminSerializer,
                        responses=SAMPLE_RESP)
    @action(detail=False, methods=['put'])
    def update_place(self, request):
        """
            장소 수정
        """
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

        # sns info 받기
        count = int(place_info['snscount'])
        sns = {}
        if(count >0):
            for i in range(count):
                snstype, snstype_name, url = place_info[str(i)].split(',')
                sns[snstype] = [snstype_name, url]                
                del place_info[str(i)]

        serializer = PlacesAdminSerializer(instance=place, data=place_info, partial=True)
    
        if serializer.is_valid():
            created_place = serializer.save()
            
            """ sns """
            # 해당 place의 sns list 가져오기
            list = SNSUrl.objects.filter(place=created_place)
            for l in list:
                snsid = str(l.snstype.id)
                # 원래 있던 snstype인 경우
                if(snsid in sns):
                    # url 비교해서 일치하면 sns info 삭제, 다르면 url update 후 삭제
                    if(l.url == sns[snsid][1]):
                        del(sns[snsid])
                    else:
                        l.url = sns[snsid][1]
                        l.save()
                        del(sns[snsid])
                                        
                else:
                    # 해당하는 타입의 sns가 삭제된 경우 db에서 삭제
                    l.delete()
        
            # 추가된 sns               
            for key,value in sns.items():
                try:
                    snstype = SNSType.objects.get(name=value[0])
                    snsurl = SNSUrl(url=value[1], place=created_place, snstype=snstype)
                    snsurl.save()
                except:
                    snstype = SNSType(name=value[0])
                    snstype.save()
                    created_snstype = SNSType.objects.get(name=value[0])
                    snsurl = SNSUrl(url=value[1], place=created_place, snstype=created_snstype)
                    snsurl.save()
                    
            photo_list = created_place.photos.all().order_by("id")

            """ pics """
            if(len(pics) > 0):
                for key,value in pics.items():
                    ext = value.name.split(".")[-1]

                    if ext not in ["jpg", "png", "gif", "jpeg",]:
                        return Response({
                            'status': 'fail',
                            'data': 'Wrong file format',
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
                        return Response({
                            'status': 'error',
                            'message': 'Unknown',
                            'code' : 400,
                        }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 'success',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        else:
            return Response({
                'status' : 'fail',
                'data' : serializer.errors,
            },status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_id='api_sdp_admin_places_check_name_overlap_get',manual_parameters=[param_place_name],
                        responses=OVERLAP_RESP)
    @action(detail=False, methods=['get'])
    def check_name_overlap(self, request):
        try:
            place_name = request.GET['place_name']
            print(place_name)
            overlap = Place.objects.filter(place_name=place_name).exists()
            print(overlap)
            return Response({
                'status': 'success',
                'data': {'overlap': overlap},
            }, status=status.HTTP_200_OK)
        except:
            return Response({
                'status': 'error',
                'message': 'Unknown',
                'code' : 400,
            }, status=status.HTTP_400_BAD_REQUEST)

class PlacesPhotoViewSet(viewsets.ModelViewSet):
    queryset = PlacePhoto.objects.all()
    serializer_class = PlacePhotoAdminSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]

    @swagger_auto_schema(operation_id='api_sdp_admin_places_placephoto_pk_get',manual_parameters=[param_pk])
    def get(self,request,pk):
        photo = PlacePhoto.objects.filter(place_id=pk)
        return Response({
                'status': 'success',
                'data': self.get_serializer(photo,many=True).data,
            }, status=status.HTTP_200_OK)

class SNSTypeViewSet(viewsets.ModelViewSet):
    """
        db에 존재하는 SNS Type을 json으로 보내 주는 api
    """

    queryset = SNSType.objects.all()
    serializer_class = SNSTypeAdminSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]
    
    @swagger_auto_schema(operation_id='api_sdp_admin_places_snstype_get')
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            'status': 'Success',
            'data': response.data,
            },status=status.HTTP_200_OK) 

class SNSUrlViewSet(viewsets.ModelViewSet):
    """
        장소에 해당하는 url을 보내주는 api
    """

    queryset = SNSUrl.objects.all()
    serializer_class = SNSUrlAdminSerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]

    @swagger_auto_schema(operation_id='api_sdp_admin_places_snsurl_get',manual_parameters=[param_pk])
    def get(self,request,pk):
        snsurl = SNSUrl.objects.filter(place_id=pk)
        return Response({
                'status': 'success',
                'data': self.get_serializer(snsurl,many=True).data,
            }, status=status.HTTP_200_OK)
    
