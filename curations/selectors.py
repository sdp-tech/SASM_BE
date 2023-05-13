# from django.db.models import Q, F
# from users.models import
from curations.models import Curation
from users.models import User
from stories.models import Story

from django.conf import settings
from django.db.models.functions import Concat, Substr
from django.db.models import Q, F, Case, When, Value, Exists, OuterRef, CharField, Aggregate


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


class CurationSelector:
    def __init__(self, user: User):
        self.user = user

    @staticmethod
    def list(search: str = ''):
        q = Q()
        q.add(Q(title__icontains=search) |
              Q(contents__icontains=search) |
              Q(story__title__icontains=search) |
              Q(story__place__place_name__icontains=search) |  # 스토리 제목 또는 내용 검색
              Q(story__place__category__icontains=search) |
              Q(story__tag__icontains=search), q.AND)

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
            writer_email=F('writer__email')
        )

        return curations

    def detail(self, curation_id: int):
        curation = Curation.objects.filter(id=curation_id).annotate(
            like_curation=Case(
                When(likeuser_set=Exists(Curation.likeuser_set.through.objects.filter(
                    curation_id=OuterRef('pk'),
                    user_id=self.user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
            writer_is_verified=F('writer__is_verified'),
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            map_image=Concat(Value(settings.MEDIA_URL),
                             F('map_photos__map'),
                             output_field=CharField()),
            writer_email=F('writer__email'),
            nickname=F('writer__nickname'),
            profile_image=Concat(Value(settings.MEDIA_URL),
                                 F('writer__profile_image'),
                                 output_field=CharField())
        )

        return curation

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

    def admin_curation_list(self):
        curations = Curation.objects.filter(
            is_released=True, writer__is_sdp_admin=True).annotate(
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

    def verified_user_curation_list(self):
        curations = Curation.objects.filter(
            is_released=True, writer__is_verified=True).annotate(
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

    # def following_user_curation_list(self):
    #     curations = Curation.objects.filter(
    #         is_released=True, writer__is_verified=True)

    #     return curations


class CuratedStoryCoordinatorSelector:
    def __init__(self, user: User):
        self.user = user

    def detail(self, curation_id: int):
        story_id_list = Curation.objects.get(id=curation_id).story.all()
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
        return Story.objects.filter(id__in=story_id_list).values('id', 'story_review', 'preview', 'writer', 'tag', 'story_likeuser_set', 'created').annotate(
            story_id=F('id'),
            place_name=F('place__place_name'),
            place_address=F('place__address'),
            place_category=F('place__category'),
            hashtags=F('tag'),
            like_story=Case(
                When(story_likeuser_set=Exists(Story.story_likeuser_set.through.objects.filter(
                    story_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
            rep_photos=GroupConcat('photos__image'),
            nickname=F('writer__nickname'),
            profile_image=Concat(Value(settings.MEDIA_URL),
                                 F('writer__profile_image'),
                                 output_field=CharField()),
            writer_email=F('writer__email')
        )


class CurationLikeSelector:
    def __init__(self):
        pass

    @staticmethod
    def likes(curation: Curation, user: User):
        if curation.likeuser_set.filter(pk=user.pk).exists():
            return True
        else:
            return False
