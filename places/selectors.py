from datetime import datetime
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.db.models import fields, Q, F, Value, CharField, Aggregate, OuterRef, Subquery

import haversine as hs

from users.models import User
from places.models import Place, PlacePhoto, SNSUrl, VisitorReview, VisitorReviewCategory


class GroupConcat(Aggregate):
    # Postgres ArrayAgg similar(not exactly equivalent) for sqlite & mysql
    # https://stackoverflow.com/questions/10340684/group-concat-equivalent-in-django
    function = 'GROUP_CONCAT'
    separator = ','

    def __init__(self, expression, distinct=False, ordering=None, **extra):
        super(GroupConcat, self).__init__(expression,
                                          distinct='DISTINCT ' if distinct else '',
                                          ordering=' ORDER BY %s' % ordering if ordering is not None else '',
                                          output_field=CharField(),
                                          **extra)

    def as_mysql(self, compiler, connection, separator=separator):
        return super().as_sql(compiler,
                              connection,
                              template='%(function)s(%(distinct)s%(expressions)s%(ordering)s%(separator)s)',
                              separator=' SEPARATOR \'%s\'' % separator)

    def as_sql(self, compiler, connection, **extra):
        return super().as_sql(compiler,
                              connection,
                              template='%(function)s(%(distinct)s%(expressions)s%(ordering)s)',
                              **extra)


class PlaceReviewCoordinatorSelector:
    def __init__(self):
        pass

    def list(place_id : int):
        place_review_qs = PlaceReviewSelector.list(
            place_id = place_id
        )

        # Concatenated field split
        for review in place_review_qs:

            if review['photos']:
                photos_list = [] # list(dict)
                review['photos'] = list(review['photos'].split(","))

                for i in range(len(review['photos'])):
                    image = {} # dict                    
                    image_url = settings.MEDIA_URL + review['photos'][i]
                    image["imgfile"] = image_url
                    photos_list.append(image)
                review['photos'] = photos_list

            if review['category']:
                category_list = [] # list(dict)
                review['category'] = list(map(int, list(review['category'].split(","))))

                for i in range(len(review['category'])):
                    category = {} # dict
                    category['category'] = review['category'][i]
                    category_list.append(category)
                review['category'] = category_list

        return place_review_qs


    def get_instance(place_review_id : int):
        place_review_qs = PlaceReviewSelector.get_instance(
            place_review_id = place_review_id
        )

        # Concatenated field split
        for review in place_review_qs:

            if review['photos']:
                photos_list = [] # list(dict)
                review['photos'] = list(review['photos'].split(","))

                for i in range(len(review['photos'])):
                    image = {} # dict                    
                    image_url = settings.MEDIA_URL + review['photos'][i]
                    image["imgfile"] = image_url
                    photos_list.append(image)
                review['photos'] = photos_list

            if review['category']:
                category_list = [] # list(dict)
                review['category'] = list(map(int, list(review['category'].split(","))))

                for i in range(len(review['category'])):
                    category = {} # dict
                    category['category'] = review['category'][i]
                    category_list.append(category)
                review['category'] = category_list

        return place_review_qs


class PlaceReviewSelector:
    def __init__(self):
        pass

    def isWriter(self, place_review_id: int, user: User):
        return VisitorReview.objects.get(id=place_review_id).visitor_name == user


    def get_instance(place_review_id: int):

        concat_category = VisitorReview.objects.filter(
                                            id = OuterRef('id')
                                            ).annotate(
                                            _category = GroupConcat('category__category')
                                            ).values('id','_category')

        concate_photo = VisitorReview.objects.filter(
                                            id = OuterRef('id')
                                            ).annotate(
                                            _photo = GroupConcat('photos__imgfile')
                                            ).values('id', '_photo')

        # GroupConcat 된 필드가 두개 이상일 경우 union 관계가 복잡해짐에 따라 subquery로 구현
        # 기존 필드의 이름과 같은 필드를 annotate 하기 위해 annotation을 나누어 수행
        place_reviews = VisitorReview.objects.filter(id=place_review_id).annotate(
            nickname = F('visitor_name__nickname'),
            writer = F('visitor_name__email')).values(
                                                    'id',
                                                    'nickname',
                                                    'place',
                                                    'contents',
                                                    'created',
                                                    'updated',
                                                    'writer'
                                                    ).annotate(
            category = Subquery(concat_category.values('_category')),
            photos = Subquery(concate_photo.values('_photo')),       
                                                    )

        return place_reviews