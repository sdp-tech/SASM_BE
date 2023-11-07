# from django.db.models import Q, F
# from users.models import
from datetime import datetime
from curations.models import Curation
from users.models import User
from stories.models import Story
from forest.models import Forest

from django.conf import settings
from django.db.models.functions import Concat, Substr
from django.db.models import Q, F, Case, When, Value, Exists, OuterRef, CharField, BooleanField, Aggregate, Count
from dataclasses import dataclass

from itertools import chain

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


@dataclass
class CurationDto:
    title: str
    contents: str
    rep_pic: str
    like_curation: bool
    writer_email: str
    nickname: str
    profile_image: str
    writer_is_verified: bool
    created: datetime
    updated: datetime
    map_image: str
    like_cnt: int
    writer_is_followed: bool = None

class CurationSelector:
    def __init__(self, user: User):
        self.user = user

    @staticmethod
    def list(search: str = '', order: str=''):
        q = Q()

        q.add(Q(title__icontains=search) |
              Q(contents__icontains=search) |
              Q(story__title__icontains=search) |
              Q(story__place__place_name__icontains=search) |  # 스토리 제목 또는 내용 검색
              Q(story__place__category__icontains=search) |
              Q(story__tag__icontains=search), q.AND)
        
        order_by_time = {'latest': '-created', 'oldest': 'created'}

        if order in order_by_time:
            order = order_by_time[order]
        else:
            order = 'created'

        curations = Curation.objects.distinct().filter(q, is_released=True).annotate(
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            writer_email=F('writer__email'),
            nickname = F('writer__nickname'),
        ).order_by(order)

        return curations

    def detail(self, curation_id: int, user: User):

        curation = Curation.objects.annotate(
            like_curation=Case(
                When(Exists(Curation.likeuser_set.through.objects.filter(
                    curation_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
            like_cnt=Count('likeuser_set'),
            is_followed = Exists(
            user.follows.through.objects.filter(
                from_user_id=user.id,
                to_user_id=OuterRef('writer_id')
                )
            ) if user.is_authenticated else Value(False),
           
        ).select_related(
            'writer'
        ).prefetch_related(
            'photos', 'map_photos'
        ).get(id=curation_id)

        curation_dto = CurationDto(
            title=curation.title,
            contents=curation.contents,
            like_curation=curation.like_curation,
            rep_pic=None,
            writer_email=curation.writer.email,
            nickname=curation.writer.nickname,
            profile_image=curation.writer.profile_image.url,
            writer_is_verified=curation.writer.is_verified,
            updated=curation.updated,
            created=curation.created,
            map_image=None,
            writer_is_followed=curation.is_followed,
            like_cnt=curation.like_cnt,
        )

        if len(curation.photos.all()) > 0:
            curation_dto.rep_pic = curation.photos.all()[0].image.url

        if len(curation.map_photos.all()) > 0:
            curation_dto.map_image = curation.map_photos.all()[0].map.url

        return curation_dto

    def rep_curation_list(self):
        curations = Curation.objects.filter(is_released=True, is_rep=True).annotate(
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            writer_email=F('writer__email')
        )

        return curations

    def admin_curation_list(search: str = ''):
        q = Q()

        q.add(Q(title__icontains=search) |
              Q(contents__icontains=search) |
              Q(story__title__icontains=search) |
              Q(story__place__place_name__icontains=search) |  # 스토리 제목 또는 내용 검색
              Q(story__place__category__icontains=search) |
              Q(story__tag__icontains=search), q.AND)

        curations = Curation.objects.distinct().filter(q, is_released=True, writer__is_sdp_admin=True).annotate(
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            writer_email=F('writer__email'),
            nickname=F('writer__nickname'),
        )

        return curations

    def verified_user_curation_list(search: str = ''):
        q = Q()

        q.add(Q(title__icontains=search) |
              Q(contents__icontains=search) |
              Q(story__title__icontains=search) |
              Q(story__place__place_name__icontains=search) |  # 스토리 제목 또는 내용 검색
              Q(story__place__category__icontains=search) |
              Q(story__tag__icontains=search), q.AND)

        curations = Curation.objects.distinct().filter(q, is_released=True, writer__is_verified=True).annotate(
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            writer_email=F('writer__email'),
            nickname = F('writer__nickname'),
        )

        return curations

    # def following_user_curation_list(self):
    #     curations = Curation.objects.filter(
    #         is_released=True, writer__is_verified=True)

    #     return curations


class CuratedStoryCoordinatorSelector:
    def __init__(self, user: User):
        self.user = user

    def detail(self, curation_id: int):
        story_id_list = Curation.objects.distinct().get(id=curation_id).story.all()
        curated_stories_qs = CuratedStorySelector.detail(
            story_id_list=story_id_list, user=self.user)

        for story in curated_stories_qs:
            if story['rep_photos'] != None:
                story['rep_photos'] = list(story['rep_photos'].split(",")[
                    :3])  # 업로드 된 사진 중 3개가 대표사진으로 자동 설정
                temp_photo_list = []

                for photo in story['rep_photos']:
                    temp_photo_list.append(settings.MEDIA_URL + str(photo))

                story['rep_photos'] = temp_photo_list

        return curated_stories_qs


class CuratedStorySelector:
    def __init__(self):
        pass

    def detail(story_id_list: list, user: User):
        return Story.objects.filter(id__in=story_id_list).values('id', 'story_review', 'preview', 'writer', 'tag', 'created').annotate(
            story_id=F('id'),
            place_name=F('place__place_name'),
            place_address=F('place__address'),
            place_category=F('place__category'),
            hashtags=F('tag'),
            like_story=Case(
                When(Exists(Story.story_likeuser_set.through.objects.filter(
                    story_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
           rep_pic=Concat(Value(settings.MEDIA_URL),  
                           F('rep_pic'),
                           output_field=CharField()),
            rep_photos=GroupConcat('photos__image'),
            nickname=F('writer__nickname'),
            profile_image=Concat(Value(settings.MEDIA_URL),
                                 F('writer__profile_image'),
                                 output_field=CharField()),
            writer_email=F('writer__email'),
            writer_is_followed = Exists(
            user.follows.through.objects.filter(
                from_user_id=user.id,
                to_user_id=OuterRef('writer_id')
                )
            ) if user.is_authenticated else Value(False),
        ).distinct()


class CurationLikeSelector:
    def __init__(self):
        pass

    @ staticmethod
    def likes(curation: Curation, user: User):
        if curation.likeuser_set.filter(pk=user.pk).exists():
            return True
        else:
            return False
        

class TotalSearchSelector:
    def __init__(self):
        pass
    
    @staticmethod
    def list(search: str='', order: str='', user: User=None):
        
        order_by_time = {'latest': '-created', 'oldest': 'created'}

        if order in order_by_time:
            order = order_by_time[order]
        else:
            order = 'created'

        #curation에 대한 검색을 하고 결과를 curations에 저장
        q_curation = Q()
        
        q_curation.add(Q(title__icontains=search) |
                       Q(contents__icontains=search) |
                       Q(story__title__icontains=search) |
                       Q(story__place__place_name__icontains=search) |
                       Q(story__place__category__icontains=search) |
                       Q(story__tag__icontains=search), q_curation.AND)

        curations = Curation.objects.distinct().filter(q_curation, is_released=True).annotate(
            user_likes=Case(
                When(Exists(Curation.likeuser_set.through.objects.filter(
                    curation_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
            like_cnt=Count('likeuser_set'),
            is_followed = Exists(
            user.follows.through.objects.filter(
                from_user_id=user.id,
                to_user_id=OuterRef('writer_id')
                )
            ) if user.is_authenticated else Value(False),
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            nickname = F('writer__nickname'),
        ).order_by(order)

        #orest에 대한 검색을 하고 결과를 forests에 저장
        q_forest = Q()
        q_forest.add(Q(title__icontains=search) |
              Q(subtitle__icontains=search) |
              Q(content__icontains=search) |
              #   Q(category__name__icontains=search) |
              #   Q(semi_categories__name__icontains=search) |
              Q(hashtags__name__icontains=search), q_forest.AND)
        
        forests = Forest.objects.distinct().annotate(
            user_likes=Case(
                When(Exists(Forest.likeuser_set.through.objects.filter(
                    forest_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
            is_followed = Exists(
            user.follows.through.objects.filter(
                from_user_id=user.id,
                to_user_id=OuterRef('writer_id')
                )
            ) if user.is_authenticated else Value(False),
            nickname=F('writer__nickname'),
        ).filter(q_forest).order_by(order)

        #story에 대한 검색을하고 결과를 stories에 저장
        q_story=Q()
        q_story.add(Q(title__icontains=search) |
              Q(place__place_name__icontains=search) |  # 스토리 제목 또는 내용 검색
              Q(place__category__icontains=search) |
              Q(tag__icontains=search), q_story.AND)
        
        stories = Story.objects.filter(q_story).annotate(
            user_likes=Case(
                When(Exists(Story.story_likeuser_set.through.objects.filter(
                    story_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
            is_followed = Exists(
            user.follows.through.objects.filter(
                from_user_id=user.id,
                to_user_id=OuterRef('writer_id')
                )
            ) if user.is_authenticated else Value(False),
            nickname=F('writer__nickname'),
        ).distinct().order_by(order)

        #curations,forests,stories 쿼리셋에서 데이터 추출하고 변환
        curations_data = [{'id': c.id, 
                           'model':c.__class__.__name__, 
                           'title':c.title, 
                           'content': c.contents,
                           'like_cnt':c.like_cnt,
                           'writer_is_followed':c.is_followed,
                           'created':c.created,
                           'rep_pic':c.rep_pic,
                           'nickname':c.nickname,
                           'user_likes': c.user_likes,
                           } for c in curations]
        
        forests_data = [{'id': f.id, 
                         'model':f.__class__.__name__, 
                         'title':f.title, 
                         'content':f.subtitle,
                         'like_cnt':f.like_cnt,
                         'writer_is_followed':f.is_followed,
                         'created':f.created.strftime("%Y-%m-%d %H:%M:%S"),
                         'rep_pic':f.rep_pic.url,
                         'nickname':f.nickname,
                         'user_likes':f.user_likes,
                         } for f in forests]
        
        stories_data = [{'id': s.id, 
                         'model':s.__class__.__name__,
                         'title':s.title, 
                         'content':s.preview,
                         'like_cnt':s.story_like_cnt,
                         'writer_is_followed':s.is_followed,
                         'created':s.created.strftime("%Y-%m-%d %H:%M:%S"),
                         'rep_pic':s.rep_pic.url,
                         'nickname':s.nickname,
                         'user_likes':s.user_likes,
                         } for s in stories]

        #세개의 데이터를 체인으로 연결
        result = list(chain(curations_data, forests_data, stories_data))

        return result