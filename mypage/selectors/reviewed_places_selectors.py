from django.db.models import F, Q, Case, When, Value, Exists, OuterRef, CharField, BooleanField, Aggregate, Subquery
from django.conf import settings
from django.db.models.functions import Concat, Substr

from users.models import User
from places.models import PlaceVisitorReview, Place

import traceback


class UserReviewedPlaceSelector:
    def __init__(self, user:User):
        self.user = user
    
    def list(self):
        user_reviews = PlaceVisitorReview.objects.filter(visitor_name__email=self.user)
        reviewed_places = Place.objects.filter(id__in=user_reviews.values('place'))
        
        return reviewed_places