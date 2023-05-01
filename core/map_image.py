from django.conf import settings

from core.exceptions import ApplicationError

import requests


class Marker:
    def __init__(self, longitude, latitude, label):
        self.longitude = longitude
        self.latitude = latitude
        self.label = label

    @staticmethod
    def query_string(marker):
        return f'&markers=type:t|size:small|pos:{marker.longitude}%20{marker.latitude}|color:blue|label:{marker.label}'


def get_static_naver_image(markers: list[Marker]):
    client_id = getattr(settings, 'NAVER_STATIC_MAP_CLIENT_ID')
    secret_key = getattr(settings, 'NAVER_STATIC_MAP_SECRET_KEY')

    url = 'https://naveropenapi.apigw.ntruss.com/map-static/v2/raster?'
    base_params = 'w=300&h=100&scale=2&public_transit'
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": secret_key,
    }

    markers_query_string = "".join(map(Marker.query_string, markers))

    response = requests.get(
        url=url + base_params + markers_query_string,
        headers=headers,
        stream=True
    )

    if not response.ok:
        raise ApplicationError("지도 이미지 다운로드에 실패했습니다.")

    return response.raw.read()
