from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from places.models import VisitorReview
from places.serializers import VisitorReviewSerializer

class PlaceReviewView(viewsets.ModelViewSet):
    queryset = VisitorReview.objects.all().order_by('-created')
    serializer_class = VisitorReviewSerializer
    permission_classes = [
        IsAuthenticated
    ]

    # @swagger_auto_schema(operation_id='api_places_review_post')
    
    @action(detail=False, methods=['post'])
    def save_review(self, request):
        '''
        장소 리뷰를 저장하는 api
        '''
        review_info = request.data
        serializer = VisitorReviewSerializer(data=review_info, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                    "status" : "success",
                    "data" : serializer.data,
                },status=status.HTTP_200_OK)
        return Response({
            "status" : "fail",
            "data" : serializer.errors,
        })