from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import exceptions

from users.models import User
from places.models import Place


class PlaceService:
    def __init__(self):
        pass

    @transaction.atomic
    def like_or_dislike(user: User, place_id: int):

        place = Place.objects.get(id=place_id)

        check_like = user in place.place_likeuser_set.all()

        if check_like:
            place.place_likeuser_set.remove(user)
            place.place_like_cnt -= 1
            place.save()
            result = 'disliked'
        else:
            place.place_likeuser_set.add(user)
            place.place_like_cnt += 1
            place.save()
            result = 'liked'

        return result