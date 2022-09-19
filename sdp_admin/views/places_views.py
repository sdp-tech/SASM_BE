from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from places.models import SNSUrl, SNSType, PlacePhoto, Place
from places.serializers import PlacePhotoSerializer, SNSUrlSerializer, MapMarkerSerializer, PlaceSerializer, PlaceDetailSerializer 


@csrf_exempt
def places_list(request):
    """
    모든 장소를 리스트, 또는 새로운 장소 생성
    """
    if request.method == 'GET':
        places = Place.objects.all()
        serializer = PlaceSerializer(
            places, many=True, context={'request': request})
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = PlaceDetailSerializer(
            data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


@csrf_exempt
def places_detail(request, pk):
    """
    장소 가져오기, 업데이트 또는 삭제
    """
    try:
        place = Place.objects.get(pk=pk)
    except Place.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = PlaceDetailSerializer(place, context={'request': request})
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = PlaceDetailSerializer(
            place, data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        place.delete()
        return HttpResponse(status=204)