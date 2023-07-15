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
        user_reviews = PlaceVisitorReview.objects.filter(visitor_name__email=self.user.email)
        reviewed_places = Place.objects.filter(id__in=user_reviews.values('place'))
        
        return reviewed_places
    

class MyPlaceSearchSelector:
    def __init__(self, user: User):
        self.user = user

    def list(self, search: str = '', filter: list = []):
        like_place = self.user.PlaceLikeUser.all()

        q = Q()
        q.add(Q(place_name__icontains=search) |
              Q(category__icontains=search), q.AND)
        
        if len(filter) > 0:
            query = None
            for element in filter:
                if query is None:
                    query = Q(category=element)
                else:
                    query = query | Q(category=element)
            q.add(query, q.AND)

        places = like_place.filter(q).order_by('-created')


                
        return places
