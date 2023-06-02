from users.models import User
from curations.models import Curation

from django.conf import settings
from django.db.models.functions import Concat
from django.db.models import Q, F, Case, When, Value, CharField, Aggregate


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
    def my_written_list(user: User):
        curations = Curation.objects.distinct().filter(writer=user).annotate(
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            writer_nickname=F('writer__nickname')
        )

        return curations

    @staticmethod
    def my_liked_list(user: User, search: str = ''):
        q = Q()
        q.add(Q(title__icontains=search) |
              Q(contents__icontains=search) |
              Q(story__title__icontains=search) |
              Q(story__place__place_name__icontains=search) |
              Q(story__place__category__icontains=search) |
              Q(story__tag__icontains=search), q.AND)

        curations = Curation.objects.distinct().filter(q, likeuser_set__in=[user]).annotate(
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            writer_nickname=F('writer__nickname')
        )

        return curations
