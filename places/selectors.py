from datetime import datetime
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.db.models import fields, Q, F, Value, CharField, Aggregate, OuterRef, Subquery
from django.db.models.functions import Concat

import haversine as hs

from users.models import User
from places.models import Place, PlaceVisitorReview

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
    

class PlaceVisitorReviewCoordinatorSelector:
    def __init__(self):
        pass

    def list(self, place_id: int):
        place = Place.objects.get(id=place_id)
        selector = PlaceReviewSelector()
        reviews_qs = PlaceReviewSelector.list(
            place=place
        )

        # category_statistics = selector.get_category_statistics(place_id=place_id)

        for review in reviews_qs:
            if review.categoryList: 
                review.categoryList = list(review.categoryList.split(","))

            if review.photoList:
                review.photoList = list(review.photoList.split(","))
                photoList = []

                for photo in review.photoList:
                    dict = {}
                    dict['imgfile'] = settings.MEDIA_URL + str(photo)
                    photoList.append(dict)

                review.photoList = photoList

            # review.category_statistics = category_statistics

        return reviews_qs


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

    def get_category_statistics(self, place_id):
        TOP_COUNTS = 3
        statistic = []

        # total count, category별 count
        place = Place.objects.get(id=place_id)
        place_review_category_total, category_count = self.count_place_review_category(place=place)
        # count순 정렬 후 TOP3 반환
        category_count = sorted(category_count.items(), key=lambda x: x[1], reverse=True)[:TOP_COUNTS]

        for i in category_count:
            l = [i[0], round(i[1]/place_review_category_total*100)]
            statistic.append(l)
        return statistic

    def count_place_review_category(self, place):
        count = 0
        category_count = {}
        l = PlaceVisitorReview.objects.filter(place=place).prefetch_related('category')

        for visitor_review_obj in l:
            # 리뷰 객체로부터 카테고리 객체 역참조
            p = visitor_review_obj.category.all()
            for visitor_review_category_obj in p:
                count+=1
                category_content = visitor_review_category_obj.category.category_content # 카테고리명
                category_count = self.is_in_category_count(category_content, category_count) # 카테고리별 선택된 횟수

        return count, category_count

    def is_in_category_count(self, category_content, category_count):
        # 기존에 인식된 카테고리면 count 증가
        if category_content in category_count.keys():
            category_count[category_content] += 1
            return category_count
        
        # 새로 인식된 카테고리면 count=1
        category_count[category_content] = 1
        return category_count

    def list(place: Place):
        # GroupConcat 된 필드가 두개 이상일 경우 union 관계가 복잡해짐에 따라 subquery로 구현
        concat_category = PlaceVisitorReview.objects.filter(
                                            id = OuterRef('id')
                                            ).annotate(
                                            _category = GroupConcat('category__category')
                                            ).values('id','_category')

        concat_photo = PlaceVisitorReview.objects.filter(
                                            id = OuterRef('id')
                                            ).annotate(
                                            _photo = GroupConcat('photos__imgfile')
                                            ).values('id', '_photo')

        reviews = PlaceVisitorReview.objects.filter(place=place).annotate(
            nickname = F("visitor_name__nickname"),
            categoryList = Subquery(concat_category.values('_category')),
            photoList = Subquery(concat_photo.values('_photo'))
        ).order_by('id')

        return reviews