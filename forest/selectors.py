from datetime import datetime
from django.db.models import Q, F, Aggregate, Value, CharField, Case, When, Exists, OuterRef, ExpressionWrapper, JSONField
from django.db.models.functions import Concat, Substr
from dataclasses import dataclass
from django.conf import settings

from users.models import User
from forest.models import Forest, Category, SemiCategory, ForestComment, ForestPhoto


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


class CategorySelector:
    def __init__(self):
        pass

    @staticmethod
    def category_list():
        return Category.objects.all()

    @staticmethod
    def semi_category_list(category: str):
        return SemiCategory.objects.filter(category=category).values('id', 'name')


@dataclass
class ForestDto:
    id: int
    title: str
    subtitle: str
    category: dict
    semi_categories: list[dict]
    writer: dict
    user_likes: bool
    like_cnt: int
    created: datetime
    updated: datetime

    content: str = None  # detail
    preview: str = None  # list

    hashtags: list[str] = None
    photos: list[str] = None


class ForestSelector:
    def __init__(self):
        pass

    @staticmethod
    def detail(forest_id: str, user: User):
        forest = Forest.objects.annotate(
            user_likes=Case(
                When(Exists(Forest.likeuser_set.through.objects.filter(
                    forest_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
        ).select_related(
            'category', 'writer'
        ).prefetch_related(
            'semicategories', 'hashtags', 'photos'
        ).get(
            id=forest_id
        )
        forest_dto = ForestDto(
            id=forest.id,
            title=forest.title,
            subtitle=forest.subtitle,
            content=forest.content,
            category={
                'id': forest.category.id,
                'name': forest.category.name,
            },
            semi_categories=[{'id': semi_category.id, 'name': semi_category.name}
                             for semi_category in forest.semicategories.all()],
            writer={
                'id': forest.writer.id,
                'nickname': forest.writer.nickname,
                'profile':  forest.writer.profile_image.url,
                'is_verified': forest.writer.is_verified,
            },
            user_likes=forest.user_likes,
            like_cnt=forest.like_cnt,
            created=forest.created.strftime('%Y-%m-%dT%H:%M:%S%z'),
            updated=forest.updated.strftime('%Y-%m-%dT%H:%M:%S%z'),

            hashtags=[hashtag.name for hashtag in forest.hashtags.all()],
            photos=[photo.image.url for photo in forest.photos.all()],
        )

        return forest_dto

    @ staticmethod
    def list(search: str,
             order: str,
             category_filter: str,
             semi_category_filters: list[str],
             user: User):
        q = Q()
        q.add(Q(title__icontains=search) |
              Q(subtitle__icontains=search) |
              Q(content__icontains=search) |
              #   Q(category__name__icontains=search) |
              #   Q(semi_categories__name__icontains=search) |
              Q(hashtags__name__icontains=search), q.AND)

        if category_filter:
            q.add(Q(category__id__iexact=category_filter), q.AND)

        semi_category_filter_q = Q()
        for semi_category_filter in semi_category_filters:
            semi_category_filter_q.add(
                Q(semicategories__id=semi_category_filter), q.OR)
        q.add(semi_category_filter_q, q.AND)

        order_pair = {'latest': '-created',
                      'oldest': 'created',
                      'hot': '-like_cnt'}

        forests = Forest.objects.distinct().annotate(
            preview=Substr('content', 1, 100),
            user_likes=Case(
                When(Exists(Forest.likeuser_set.through.objects.filter(
                    forest_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
        ).select_related(
            'category', 'writer'
        ).prefetch_related(
            'semicategories', 'hashtags', 'photos'
        ).filter(q).order_by(order_pair[order])

        forest_dtos = [ForestDto(
            id=forest.id,
            title=forest.title,
            subtitle=forest.subtitle,
            preview=forest.preview,
            category={
                'id': forest.category.id,
                'name': forest.category.name,
            },
            semi_categories=[{'id': semi_category.id, 'name': semi_category.name}
                             for semi_category in forest.semicategories.all()],
            writer={
                'id': forest.writer.id,
                'nickname': forest.writer.nickname,
                'profile':  forest.writer.profile_image.url,
                'is_verified': forest.writer.is_verified,
            },
            user_likes=forest.user_likes,
            like_cnt=forest.like_cnt,
            created=forest.created.strftime('%Y-%m-%dT%H:%M:%S%z'),
            updated=forest.updated.strftime('%Y-%m-%dT%H:%M:%S%z'),

            hashtags=[hashtag.name for hashtag in forest.hashtags.all()],
            photos=[photo.image.url for photo in forest.photos.all()],
        ) for forest in forests]

        return forest_dtos

    @ staticmethod
    def likes(forest: Forest, user: User):
        return forest.likeuser_set.filter(pk=user.pk).exists()


class ForestCommentSelector:
    def __init__(self):
        pass

    @ staticmethod
    def list(forest: Forest, user: User):
        forest_comments = ForestComment.objects.filter(forest=forest).values('id', 'content', 'like_cnt', 'created', 'updated').annotate(
            writer_nickname=F('writer__nickname'),
            writer_email=F('writer__email'),
            writer_profile=Concat(Value(settings.MEDIA_URL),
                                  F('writer__profile_image'),
                                  output_field=CharField()),
            user_likes=Case(
                When(Exists(ForestComment.likeuser_set.through.objects.filter(
                    forestcomment_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
        ).order_by('id')

        return forest_comments

    @ staticmethod
    def likes(forest_comment: ForestComment, user: User):
        return forest_comment.likeuser_set.filter(pk=user.pk).exists()
