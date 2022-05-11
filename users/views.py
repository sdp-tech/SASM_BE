from urllib import response
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import permission_classes, authentication_classes, api_view
from .serializers import *


# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def Login(request):
    if request.method == 'POST':
        serializer = UserLoginSerializer(data=request.data)

        if not serializer.is_valid(raise_exception=True):
            return Response({"message": "Request Body Error"}, status=status.HTTP_409_CONFLICT)
        if serializer.validated_data['email'] == "None":
            return Response({"message": 'fail'}, status=status.HTTP_200_OK)
        response = {
            'success': True,
            'token': serializer.data['token']
        }
        return Response(response, status=status.HTTP_200_OK)

# @permission_classes([AllowAny])
# class Login(generics.GenericAPIView):
#     serializer_class = UserLoginSerializer
# 
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
# 
#         if not serializer.is_valid(raise_exception=True):
#             return Response({"message": "Request Body Error."}, status=status.HTTP_409_CONFLICT)
# 
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data
#         if user['email'] == "None":
#             return Response({"message": "fail"}, status=status.HTTP_401_UNAUTHORIZED)
# 
#         return Response(
#             {
#                 "user": UserSerializer(
#                     user, context=self.get_serializer_context()
#                 ).data,
#                 "token": user['tokken']
#             }
#         )