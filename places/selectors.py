from datetime import datetime
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.db.models import fields, Q, F, Value, CharField, Aggregate, OuterRef, Subquery

import haversine as hs

from users.models import User
from places.models import Place, PlaceVisitorReview

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

class PlaceReviewSelector:
    def __init__(self):
        pass

    def isWriter(self, place_review_id: int, user: User):
        return PlaceVisitorReview.objects.get(id=place_review_id).visitor_name == user