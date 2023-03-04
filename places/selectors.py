from datetime import datetime
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.db.models import fields, Q, F, Value, CharField, Aggregate, OuterRef, Subquery

import haversine as hs

from users.models import User
from places.models import Place

    
class PlaceSelector:
    def __init__(self):
        pass

    def lat_lon():
        place_lat_lon = Place.objects.values(
            'id',
            'place_name',
            'latitude',
            'longitude'
        )

        return place_lat_lon