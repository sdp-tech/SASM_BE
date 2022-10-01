from rest_framework import generics
from rest_framework import permissions
from rest_framework import viewsets
from places.models import Place, PlacePhoto
from places.serializers import PlaceDetailSerializer, PlaceSerializer
from functools import partial

from django.core.files.images import ImageFile
from django.http import JsonResponse


from stories.models import StoryPhoto, Story
from ..serializers.places_serializers import PlacePhotoSerializer
from core.permissions import IsSdpStaff


#serializer에 partial=True를 주기위한 Mixin
class SetPartialMixin:
    def get_serializer_class(self, *args, **kwargs):
        serializer_class = super().get_serializer_class(*args, **kwargs)
        return partial(serializer_class, partial=True)


class PlaceAdmin(SetPartialMixin, viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [permissions.AllowAny]


class PlaceList(generics.ListCreateAPIView):
    """
    모든 장소를 리스트, 또는 새로운 장소 생성
    """
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PlaceDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    장소 가져오기, 업데이트 또는 삭제
    """
    queryset = Place.objects.all()
    serializer_class = PlaceDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):            
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


# TODO: stories/views.py와 코드 중복, core로 빼기
class PlacePagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'    



class PlaceViewSet(viewsets.ModelViewSet):
    """
    모든 스토리를 리스트, 또는 새로운 스토리 생성
    스토리 가져오기, 업데이트 또는 삭제
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


class StoryPhotoViewSet(CreateAPIView):
    queryset = PlacePhoto.objects.all()
    serializer_class = PlacePhotoSerializer