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

'''
class ConcatSubquery(Subquery):
    # https://leonardoramirezmx.medium.com/how-to-concat-subquery-on-django-orm-cce32371a693
    """ Concat multiple rows of a subquery with only one column in one cell.
        Subquery must return only one column.
    >>> store_produts = Product.objects.filter(
                                            store=OuterRef('pk')
                                        ).values('name')
    >>> Store.objects.values('name').annotate(
                                            products=ConcatSubquery(store_produts)
                                        )
    <StoreQuerySet [{'name': 'Dog World', 'products': ''}, {'name': 'AXÉ, Ropa Deportiva
    ', 'products': 'Playera con abertura ojal'}, {'name': 'RH Cosmetiques', 'products':
    'Diabecreme,Diabecreme,Diabecreme,Caída Cabello,Intensif,Smooth,Repairing'}...
    """
    template = 'ARRAY_TO_STRING(ARRAY(%(subquery)s), %(separator)s)'
    output_field = fields.CharField()

    def __init__(self, *args, separator=', ', **kwargs):
        self.separator = separator
        super().__init__(*args, separator, **kwargs)

    def as_sql(self, compiler, connection, template=None, **extra_context):
        extra_context['separator'] = '%s'
        sql, sql_params = super().as_sql(compiler, connection, template, **extra_context)
        sql_params = sql_params + (self.separator, )
        return sql, sql_params
'''    

@dataclass
class PlaceDto:
    id: int
    place_name: str
    category: str
    mon_hours: str
    tues_hours: str
    mon_hours: str
    wed_hours: str
    thurs_hours: str
    fri_hours: str
    sat_hours: str
    sun_hours: str
    place_review: str
    address: str
    rep_pic: str
    short_cur: str
    latitude: float
    longitude: float
    place_sns_url: list[dict]
    story_id: int
    # place_like: str
    category_statistics: float


class PlaceCoordinatorSelector:
    def __init__(self, user: User):
        self.user = user
    
    def list(user: str, left: float, right: float, search: str, category: str):
        places_qs = PlaceSelector.list(
            left = left,
            right = right,
            search = search,
            category = category
        )

        # TODO: PlaceSelector annotation으로 구현
        # 좋아요를 누른 모든 user id를 담은 리스트 생성
        for place in places_qs:
            if place.place_like:
                place.place_like = list(map(int, list(place.place_like.split(","))))
                
                # 리스트에 user id가 있다면(=좋아요를 눌렀다면) ok, 아니라면 none
                if user in place.place_like:
                    place.place_like = 'ok'
                else:
                    place.place_like = 'none'
            
            else: place.place_like = 'none'
        

        # 사용자 위치로부터 거리 계산
        for place in places_qs:
            my_location = (left, right)
            place_location = (place.latitude, place.longitude)
            distance = hs.haversine(my_location, place_location)
            
            place.distance = distance
        
        
        # 오늘 요일의 영업 시간 표시
        days = ['mon_hours','tues_hours','wed_hours','thurs_hours','fri_hours','sat_hours','sun_hours']
        
        for place in places_qs:
            today = datetime.today().weekday()
            today_open_hour = days[today]

            place.open_hours = place.__dict__[today_open_hour]


        # rep pic url 생성
        for place in places_qs:
            place.rep_pic = settings.MEDIA_URL + place.rep_pic.name  

        return places_qs      


    def detail(user: str, place_id: int):
        place_qs = PlaceSelector.detail(
            place_id = place_id
        )

        dto = PlaceDto(
            id = place_qs[0].id,
            place_name = place_qs[0].place_name,
            category = place_qs[0].category,
            mon_hours = place_qs[0].mon_hours,
            tues_hours = place_qs[0].tues_hours,
            wed_hours = place_qs[0].wed_hours,
            thurs_hours = place_qs[0].thurs_hours,
            fri_hours = place_qs[0].fri_hours,
            sat_hours = place_qs[0].sat_hours,
            sun_hours = place_qs[0].sun_hours,
            place_review = place_qs[0].place_review,
            address = place_qs[0].address,
            rep_pic = place_qs[0].rep_pic,
            short_cur = place_qs[0].short_cur,
            latitude = place_qs[0].latitude,
            longitude = place_qs[0].longitude,
            place_sns_url = [],
            story_id = place_qs[0].story_id,
            # place_like = '',
            category_statistics = 0,
        )

        # 오늘 요일의 영업 시간 표시
        days = ['mon_hours','tues_hours','wed_hours','thurs_hours','fri_hours','sat_hours','sun_hours']
        
        today = datetime.today().weekday()
        today_open_hour = days[today]

        dto.open_hours = place_qs[0].__dict__[today_open_hour]


        # 사진 리스트
        photos_list = [] # Dto로 전달 될 필드
        photos = PlacePhoto.objects.filter(place = place_qs[0])

        for i in range(len(photos)):
            image_url = settings.MEDIA_URL + photos[i].image.name
            image = {}
            image["image"] = image_url
            photos_list.append(image)

        dto.photos = photos_list


        # sns url 리스트
        sns_url_list = [] # Dto로 전달 될 필드
        sns_urls = SNSUrl.objects.filter(place = place_qs[0])

        for i in range(len(sns_urls)):
            sns_url = sns_urls[i].url
            sns = {}
            sns["url"] = sns_url
            sns_url_list.append(sns)

        dto.place_sns_url = sns_url_list        


        # TODO: PlaceSelector annotation으로 구현
        # 좋아요를 누른 모든 user id를 담은 리스트 생성
        if place_qs[0].place_like:
            place_qs[0].place_like = [1, 2, 3]
            list(map(int, list(place_qs[0].place_like.split(","))))

            # 리스트에 user id가 있다면(=좋아요를 눌렀다면) ok, 아니라면 none
            if user in place_qs[0].place_like:
                dto.place_like = 'ok'
            else:
                dto.place_like = 'none'
        else:
            dto.place_like = 'none'
        
        
        # TODO: category statistics logic
        dto.category_statistics = 0.5

        return dto


    def likers(place_id : int):
        likers_qs = PlaceSelector.likers(
            place_id = place_id
        )

        # rep pic url 생성
        for i in range(len(likers_qs)):
            likers_qs[i]['profile_image'] = settings.MEDIA_URL + likers_qs[i]['profile_image']

        return likers_qs
    

class PlaceSelector:
    def __init__(self):
        pass

    def list(left: float, right: float, search: str, category: str):
        
        # 장소 검색어
        q = Q()
        q.add(Q(place_name__icontains=search), q.AND)
        
        # 카테고리 필터
        query = None
        for i in category:
            if query is None:
                query = Q(category=i)
            else:
                query = query | Q(category=i) # 결과 더해서 필터링

                    
        places = Place.objects.filter(q).annotate(
            place_like = GroupConcat('place_likeuser_set'),
            open_hours = Value(''),
            distance = Value(0)
            )
        
        return places


    def detail(place_id: int):

        places = Place.objects.filter(id=place_id).annotate(
            place_like = GroupConcat('place_likeuser_set'),
            story_id = F('story__id')
            )
        
        return places  


    def lat_lon():

        map_mark = Place.objects.values(
            'id',
            'place_name',
            'latitude',
            'longitude'
        )

        return map_mark


    def likers(place_id: int):

        users = Place.objects.prefetch_related(
                            'place_likeuser_set').get(
                            id=place_id).place_likeuser_set.values(
                            'id',
                            'gender',
                            'nickname',
                            'birthdate',
                            'email',
                            'address',
                            'profile_image',
                            'is_sdp'
                            )
        
        return users


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


    def get_created(place_id : int):
        place_review_qs = PlaceReviewSelector.get_created(
            place_id = place_id
        )
        print("~~~~3333", place_review_qs)

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

    def list(place_id: int):

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
        place_reviews = VisitorReview.objects.annotate(
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


    def get_created(place_id: int):
        
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
        place_reviews = VisitorReview.objects.filter(place_id=place_id).annotate(
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
