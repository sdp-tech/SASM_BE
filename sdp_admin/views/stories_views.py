import io
import time
from django.core.files.images import ImageFile
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from drf_yasg.utils import swagger_auto_schema
from stories.models import StoryPhoto, Story
from ..serializers.stories_serializers import StoryPhotoSerializer, StorySerializer
from core.permissions import IsSdpStaff
from sasmproject.swagger import StoryViewSet_post_params

# TODO: stories/views.py와 코드 중복, core로 빼기
class StoryPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'page_size'


class StoryViewSet(viewsets.ModelViewSet):
    """
    모든 스토리를 리스트, 또는 새로운 스토리 생성
    스토리 가져오기, 업데이트 또는 삭제
    """

    queryset = Story.objects.all().order_by('id')
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated, IsSdpStaff]
    pagination_class = StoryPagination

    @swagger_auto_schema(operation_id='api_sdp_admin_stories_get')
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            'status': 'Success',
            'data': response.data,
            },status=status.HTTP_200_OK)
    
    @swagger_auto_schema(operation_id='api_sdp_admin_stories_post')
    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({
            'status': 'Success',
            },status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_sdp_admin_stories_put')
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response({
            'status': 'Success',
            },status=status.HTTP_200_OK)

    @swagger_auto_schema(operation_id='api_sdp_admin_stories_photo_post',request_body=StoryViewSet_post_params)
    @action(detail=False, methods=['post'])
    def photos(self, request):
        file_obj = request.FILES['file']
        ext = file_obj.name.split(".")[-1]

        if ext not in ["jpg", "png", "gif", "jpeg", ]:
            return Response({
                'status': 'fail',
                'data': {'photo' : 'Wrong file format'},
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            caption = request.POST['caption']
            place_name = request.POST['place_name']

            file_path = '{}/{}.{}'.format(place_name,
                                            'content' + str(int(time.time())), ext)
            image = ImageFile(io.BytesIO(file_obj.read()), name=file_path)

            photo = StoryPhoto(caption=caption, image=image)
            photo.save()
        except:
            return Response({
                'status': 'error',
                'message': 'Unknown',
                'code' : 400,
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = StoryPhotoSerializer(photo)
        print(serializer.data['image'])
        return Response({
            'status': 'success',
            'data': {'location': serializer.data['image']},
        }, status=status.HTTP_201_CREATED)


class StoryPhotoViewSet(CreateAPIView):
    queryset = StoryPhoto.objects.all()
    serializer_class = StoryPhotoSerializer


# @csrf_exempt
# def snippet_list(request):
#     """
#     List all code snippets, or create a new snippet.
#     """
#     if request.method == 'GET':
#         snippets = Snippet.objects.all()
#         serializer = SnippetSerializer(snippets, many=True)
#         return JsonResponse(serializer.data, safe=False)
#     elif request.method == 'POST':
#         data = JSONParser().parse(request)
#         serializer = SnippetSerializer(data=data)
#         if serializer.is_valid():
#             serializer.save()
#             return JsonResponse(serializer.data, status=201)
#         return JsonResponse(serializer.errors, status=400)
