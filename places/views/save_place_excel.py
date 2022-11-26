import boto3
import json
import requests
# import pandas as pd

from django.conf import settings

aws_access_key_id = getattr(settings,'AWS_ACCESS_KEY_ID')
aws_secret_access_key = getattr(settings,'AWS_SECRET_ACCESS_KEY')
kakao_rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')

def get_s3(place,num):
    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)
        obj_list = s3.list_objects(Bucket='sasm-bucket',Prefix='media/places/{}'.format(place))
        content_list = obj_list['Contents']
        for content in content_list:
            if str(content['Key']).find('{}/'.format(place) + str(num) + '.') != -1:
                result = content['Key']
                break
        print(place)
        print(result)
        ext = result.split(".")[-1]
        return ext
    except Exception as e:
        print('에러',e)

def addr_to_lat_lon(addr):
    url = 'https://dapi.kakao.com/v2/local/search/address.json?query={address}'.format(address=addr)
    headers = {"Authorization": "KakaoAK " + kakao_rest_api_key}
    result = json.loads(str(requests.get(url, headers=headers).text))
    match_first = result['documents'][0]['address']
    x=float(match_first['x'])
    y=float(match_first['y'])
    return (x, y)

# @swagger_auto_schema(operation_id='func_places_save_place_get', method='get',responses={200:'success'},security=[])
# @api_view(['GET'])
# def save_place_db(request):
#     '''
#         SASM_DB 엑셀파일을 읽어 Place,PlacePhoto,SNS를 DB에 저장하는 함수
#     '''
#     df = pd.read_excel("SASM_DB.xlsx", engine="openpyxl")
#     df = df.fillna('')
#     for dbfram in df.itertuples():
#         place_name = dbfram[1]
#         ext = get_s3(place_name, "rep")
        
#         obj = Place.objects.create(
#             place_name=dbfram[1],
#             category=dbfram[2],
#             vegan_category=dbfram[3],
#             tumblur_category=dbfram[4],
#             reusable_con_category=dbfram[5],
#             pet_category=dbfram[6],
#             mon_hours=dbfram[7],
#             tues_hours=dbfram[8],
#             wed_hours=dbfram[9],
#             thurs_hours=dbfram[10],
#             fri_hours=dbfram[11],
#             sat_hours=dbfram[12],
#             sun_hours=dbfram[13],
#             etc_hours=dbfram[14],
#             place_review=dbfram[15],
#             address=dbfram[16],
#             longitude=addr_to_lat_lon(dbfram[16])[0],
#             latitude=addr_to_lat_lon(dbfram[16])[1],
#             short_cur=dbfram[17],
#             phone_num=dbfram[18],
#             rep_pic = 'places/{}/rep.{}'.format(place_name, ext),
#             )
#         obj.save()
#         id = obj.id
#         for j in range(1,4):
#             ext = get_s3(place_name, str(j))            
#             img = PlacePhoto.objects.create(
#                 image = 'places/{}/{}.{}'.format(place_name, str(j), ext),
#                 place_id=id,
#                 )
#             img.save()
        
#         k = 19
#         while(True):
#             if(k<25 and len(dbfram[k])!=0):
#                 sns_type = dbfram[k]
#                 if SNSType.objects.filter(name=sns_type).exists():
#                     obj1 = SNSUrl.objects.create(
#                         snstype_id=SNSType.objects.get(name=sns_type).id,
#                         url = dbfram[k+1],
#                         place_id=id,
#                     )
#                     obj1.save()
#                 else:
#                     obj2 = SNSType.objects.create(
#                         name = sns_type,
#                     )
#                     obj2.save()
#                     obj3 = SNSUrl.objects.create(
#                         snstype_id=obj2.id,
#                         url = dbfram[k+1],
#                         place_id=id,
#                     )
#                     obj3.save()
#                 k+=2
#             else:
#                 break
#     return Response({'msg': 'success'})