from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from places.models import Place
from places.services import PlaceCoordinatorService
from places.selectors import PlaceSnsTypeSelector, PlaceAddressOverlapCheckSelector
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class PlaceCreateApi(APIView):
    permission_classes = (IsAuthenticated,)

    class PlaceCreateInputSerializer(serializers.Serializer):
        place_name = serializers.CharField()
        category = serializers.CharField()
        vegan_category = serializers.CharField(allow_null=True)
        tumblur_category = serializers.BooleanField(allow_null=True)
        reusable_con_category = serializers.BooleanField(allow_null=True)
        pet_category = serializers.BooleanField(allow_null=True)
        mon_hours = serializers.CharField()
        tues_hours = serializers.CharField()
        wed_hours = serializers.CharField()
        thurs_hours = serializers.CharField()
        fri_hours = serializers.CharField()
        sat_hours = serializers.CharField()
        sun_hours = serializers.CharField()
        etc_hours = serializers.CharField()
        place_review = serializers.CharField()
        address = serializers.CharField()
        short_cur = serializers.CharField()
        phone_num = serializers.CharField()
        rep_pic = serializers.ImageField()
        imageList = serializers.ListField()
        snsList = serializers.ListField(required=False)

        class Meta:
            examples = {
                'place_name': '안녕 상점',
                'category': '식당 및 카페',
                'vegan_category': '비건',
                'tumblur_category': True,
                'reusable_con_category': True,
                'pet_category': True,
                'mon_hours': '09:00 ~ 22:00',
                'tues_hours': '09:00 ~ 22:00',
                'wed_hours': '09:00 ~ 22:00',
                'thurs_hours': '09:00 ~ 22:00',
                'fri_hours': '09:00 ~ 22:00',
                'sat_hours': '09:00 ~ 22:00',
                'sun_hours': '09:00 ~ 22:00',
                'etc_hours': '공휴일 09:00 ~ 22:00',
                'place_review': '\"붉은 벽돌 외관에서의 담소\"',
                'address': '서울 서대문구 연희로5길 22',
                'short_cur': '연남장(場) 연희동 카페는 공간이 널찍하고 층고가 높습니다.',
                'phone_num': '02-3141-7977',
                'rep_pic': '< IMAGE FILE BINARY >',
                'imageList': ['<IMAGE FILE BINARY>', '<IMAGE FILE BINARY>'],
                'snsList': ['1,https://instagram.com/abc/', '2,https://www.sasm.co.kr/'],
            }

    @swagger_auto_schema(
        request_body=PlaceCreateInputSerializer,
        security=[],
        operation_id='장소 제보하기',
        operation_description='''
            일반 유저를 위한 장소 제보하기 기능입니다.<br/>
            vegan_category, tumblur_category, reusable_con_category, pet_category의 경우, "알 수 없는 경우"에 해당하는 경우 null 값을 넘겨주면 됩니다.<br/>
            SNS 정보는 "SNS 타입 id(예: 1),https://instagram.com/abc/" 형태의 문자열로 snsList 필드에 담아보내면 됩니다. <br/>
            SNS 타입 종류 리스트는 GET: /places/sns_types/을 통해서 가져올 수 있습니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"id": 1}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
        serializer = self.PlaceCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        place = PlaceCoordinatorService.create(
            place_name=data.get('place_name'),
            category=data.get('category'),
            vegan_category=(data.get('vegan_category') if data.get(
                'vegan_category') != 'null' else None),
            tumblur_category=data.get('tumblur_category'),
            reusable_con_category=data.get('reusable_con_category'),
            pet_category=data.get('pet_category'),
            mon_hours=data.get('mon_hours'),
            tues_hours=data.get('tues_hours'),
            wed_hours=data.get('wed_hours'),
            thurs_hours=data.get('thurs_hours'),
            fri_hours=data.get('fri_hours'),
            sat_hours=data.get('sat_hours'),
            sun_hours=data.get('sun_hours'),
            etc_hours=data.get('etc_hours'),
            place_review=data.get('place_review'),
            address=data.get('address'),
            short_cur=data.get('short_cur'),
            phone_num=data.get('phone_num'),
            rep_pic=data.get('rep_pic'),
            imageList=data.get('imageList', []),
            snsList=data.get('snsList', []),
        )

        return Response({
            'status': 'success',
            'data': {'id': place.id},
        }, status=status.HTTP_201_CREATED)


class PlaceUpdateApi(APIView):
    permission_classes = (IsAuthenticated,)

    class PlaceUpdateInputSerializer(serializers.Serializer):
        place_name = serializers.CharField()
        category = serializers.CharField()
        vegan_category = serializers.CharField(allow_null=True)
        tumblur_category = serializers.BooleanField(allow_null=True)
        reusable_con_category = serializers.BooleanField(allow_null=True)
        pet_category = serializers.BooleanField(allow_null=True)
        mon_hours = serializers.CharField()
        tues_hours = serializers.CharField()
        wed_hours = serializers.CharField()
        thurs_hours = serializers.CharField()
        fri_hours = serializers.CharField()
        sat_hours = serializers.CharField()
        sun_hours = serializers.CharField()
        etc_hours = serializers.CharField()
        place_review = serializers.CharField()
        address = serializers.CharField()
        short_cur = serializers.CharField()
        phone_num = serializers.CharField()
        rep_pic = serializers.ImageField()
        imageList = serializers.ListField()
        snsList = serializers.ListField(required=False)

    @swagger_auto_schema(
        request_body=PlaceUpdateInputSerializer,
        security=[],
        operation_id='장소 수정하기',
        operation_description='일반 유저가 장소 정보를 수정할 수 있는 기능입니다. rep_pic 필드의 경우 변경하려 하지 않을 시 해당 필드를 input데이터에 포함하지 마세요',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"message": "장소 정보가 업데이트되었습니다."}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def patch(self, request, place_id):
        place = get_object_or_404(Place, id=place_id)

        serializer = self.PlaceUpdateInputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        update_data = {
            'place_name': data.get('place_name'),
            'category': data.get('category'),
            'vegan_category' : (data.get('vegan_category') if data.get('vegan_category') != 'null' else None),
            'tumblur_category' : data.get('tumblur_category'),
            'reusable_con_category' : data.get('reusable_con_category'),
            'pet_category':data.get('pet_category'),
            'mon_hours':data.get('mon_hours'),
            'tues_hours':data.get('tues_hours'),
            'wed_hours':data.get('wed_hours'),
            'thurs_hours':data.get('thurs_hours'),
            'fri_hours':data.get('fri_hours'),
            'sat_hours':data.get('sat_hours'),
            'sun_hours':data.get('sun_hours'),
            'etc_hours':data.get('etc_hours'),
            'place_review':data.get('place_review'),
            'address':data.get('address'),
            'short_cur':data.get('short_cur'),
            'phone_num':data.get('phone_num'),
            'rep_pic': data.get('rep_pic') or place.rep_pic,
            'imageList': data.get('imageList', []),
            'snsList':data.get('snsList', []),
        }

        place_coordinator_service = PlaceCoordinatorService(request.user)
        try:
            place_coordinator_service.update_place(place_id, update_data)
        except Place.DoesNotExist as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': 'success', 'data': {'message': '장소 정보가 업데이트되었습니다.'}})


def get_paginated_response(*, pagination_class, serializer_class, queryset, request, view):
    paginator = pagination_class()

    page = paginator.paginate_queryset(queryset, request, view=view)

    if page is not None:
        serializer = serializer_class(page, many=True)
    else:
        serializer = serializer_class(queryset, many=True)

    return Response({
        'status': 'success',
        'data': paginator.get_paginated_response(serializer.data).data,
    }, status=status.HTTP_200_OK)


class PlaceSnsTypeListApi(APIView):
    permission_classes = (AllowAny,)

    class Pagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'

    class PlaceSnsTypeListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()

    @ swagger_auto_schema(
        operation_id='장소 SNS 타입 리스트',
        operation_description='''
            사용 가능한 SNS 타입 리스트를 반환합니다.
        ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        'id': 1,
                        'name': '인스타그램',
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def get(self, request):
        sns_types = PlaceSnsTypeSelector.list()

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.PlaceSnsTypeListOutputSerializer,
            queryset=sns_types,
            request=request,
            view=self
        )

class PlaceAddressOverlapCheckApi(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        overlap = PlaceAddressOverlapCheckSelector.check(request = request)

        return Response({
            'status': 'success',
            'data': {'overlap':overlap},
        }, status = status.HTTP_200_OK)