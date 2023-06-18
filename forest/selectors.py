from django.conf import settings
from django.db.models import Q, F, Aggregate, Value, CharField, Case, When, Exists, OuterRef, Subquery
from django.db.models.functions import Concat, Substr

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


class ForestSelector:
    def __init__(self):
        pass

    @staticmethod
    def detail(forest_id: str, user: User):
        forest = Forest.objects.values('id', 'title', 'subtitle', 'content', 'like_cnt', 'created').annotate(
            writer_is_verified=F('writer__is_verified'),
            writer_nickname=F('writer__nickname'),
            writer_profile=Concat(Value(settings.MEDIA_URL),
                                  F('writer__profile_image'),
                                  output_field=CharField()),
            user_likes=Case(
                When(Exists(Forest.likeuser_set.through.objects.filter(
                    forest_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
            rep_pic=Subquery(
                # TODO: filter 대신 get/first 쓸 경우 아래 에러 발생
                # ValueError: This queryset contains a reference to an outer query and may only be used in a subquery.
                # => django eager query 찾아보기
                ForestPhoto.objects.filter(forest=OuterRef('id')).annotate(
                    _image=Concat(Value(settings.MEDIA_URL),
                                  F('image'),
                                  output_field=CharField())
                ).values('_image')[:1]
            ),
            # TODO:
            # 아래 코드는 forest 하위 photo가 여러개일 경우 각 photo마다 row가 반환된다. 첫번째 사진에 대한 row가 반환되지 않음
            # 다른 코드들에 아래와 유사한 코드가 있을 경우 수정 필요
            # rep_pic=Case(
            #     When(
            #         photos__image=None,
            #         then=None
            #     ),
            #     default=Concat(Value(settings.MEDIA_URL),
            #                    F('photos__image'),
            #                    output_field=CharField())
            # ),
            category=F('category__name'),
            semi_categories=Subquery(
                Forest.objects.filter(id=OuterRef('id')).annotate(
                    _semi_categories=GroupConcat('semicategories__name')
                ).values('_semi_categories')
            ),
            hashtags=Subquery(
                Forest.objects.filter(id=OuterRef('id')).annotate(
                    _hashtags=GroupConcat('hashtags__name')
                ).values('_hashtags')
            ),
        ).get(id=forest_id)

        forest['hashtags'] = forest['hashtags'].split(
            ',') if forest['hashtags'] else []
        forest['semi_categories'] = forest['semi_categories'].split(
            ',') if forest['semi_categories'] else []

        return forest

    @staticmethod
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

        forests = Forest.objects.distinct().filter(q).values(
            'id', 'title', 'subtitle', 'like_cnt', 'created').annotate(
            preview=Substr('content', 1, 100),
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
            user_likes=Case(
                When(Exists(Forest.likeuser_set.through.objects.filter(
                    forest_id=OuterRef('pk'),
                    user_id=user.pk
                )),
                    then=Value(1)),
                default=Value(0),
            ),
            writer_is_verified=F('writer__is_verified'),
            writer_nickname=F('writer__nickname'),
            writer_profile=Concat(Value(settings.MEDIA_URL),
                                  F('writer__profile_image'),
                                  output_field=CharField()),
        ).order_by(order_pair[order])

        return forests

    @staticmethod
    def likes(forest: Forest, user: User):
        return forest.likeuser_set.filter(pk=user.pk).exists()


class ForestCommentSelector:
    def __init__(self):
        pass

    @staticmethod
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

    @staticmethod
    def likes(forest_comment: ForestComment, user: User):
        return forest_comment.likeuser_set.filter(pk=user.pk).exists()
