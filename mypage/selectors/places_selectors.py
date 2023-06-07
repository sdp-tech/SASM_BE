from django.db.models import F, Q, Case, When, Value, Exists, OuterRef, CharField, BooleanField, Aggregate, Subquery
from django.conf import settings
from django.db.models.functions import Concat, Substr

from users.models import User
from places.models import PlaceVisitorReview, Place

import traceback


class UserReviewedSelector:
    def __init__(self, user:User):
        self.user = user
    
    def list(self):
        reviewedplaces = PlaceVisitorReview.objects.filter(visitor_name__email=self.user)

        return reviewedplaces