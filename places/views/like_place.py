from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from places.models import Place
from places.serializers import PlaceSerializer
from users.models import User
from users.serializers import UserSerializer
from sasmproject.swagger import PlaceLikeView_post_params

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