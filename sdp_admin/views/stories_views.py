from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from stories.models import StoryPhoto, Story
from stories.serializers import StoryDetailSerializer, StoryListSerializer


@csrf_exempt
def storeis_list(request):
    """
    모든 스토리를 리스트, 또는 새로운 스토리 생성
    """
    if request.method == 'GET':
        stories = Story.objects.all()
        serializer = StoryListSerializer(
            stories, many=True, context={'request': request})
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = StoryDetailSerializer(
            data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


@csrf_exempt
def stories_detail(request, pk):
    """
    스토리 가져오기, 업데이트 또는 삭제
    """
    try:
        story = Story.objects.get(pk=pk)
    except Story.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = StoryDetailSerializer(story, context={'request': request})
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = StoryDetailSerializer(
            story, data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        story.delete()
        return HttpResponse(status=204)