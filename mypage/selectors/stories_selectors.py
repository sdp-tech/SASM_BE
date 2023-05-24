from django.db.models import F, Q, Aggregate, CharField
from django.conf import settings

from users.models import User
from stories.models import Story


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

def append_media_url(rest):
    return settings.MEDIA_URL + rest

class UserStorySelector:
    def __init__(self, user: User):
        self.user = user

    def list(self, search: str = '', filter: list = []):
        like_story = self.user.StoryLikeUser.all()

        q = Q()
        q.add(Q(title__icontains=search) |
              Q(place__place_name__icontains=search) |
              Q(place__category__icontains=search) |
              Q(tag__icontains=search), q.AND)
        
        if len(filter) > 0:
            query = None
            for element in filter:
                if query is None:
                    query = Q(place__category=element)
                else:
                    query = query | Q(place__category=element)
            q.add(query, q.AND)

        stories = like_story.filter(q).annotate(
            place_name=F('place__place_name'),
            category=F('place__category'),
            writer_is_verified=F('writer__is_verified'),
            nickname=F('writer__nickname'),
            # profile=Concat(Value(settings.MEDIA_URL),
            #                F('writer__profile_image'),
            #                output_field=CharField()),
            extra_pics=GroupConcat('photos__image'),
        ).order_by('-created')

        for story in stories:
            story.rep_pic = story.rep_pic.url
            if story.extra_pics is not None:
                story.extra_pics = map(
                    append_media_url, story.extra_pics.split(',')[:3])

        return stories

    def get_by_comment(self):

        my_story_comments = self.user.story_comments.filter(
            writer=self.user).values_list('story')
        story_filter = [y for x in set(my_story_comments) for y in x]

        stories = Story.objects.filter(id__in=story_filter).annotate(
            place_name=F('address__place_name')
        ).order_by('created')

        return stories


class UserCreatedStorySelector:
    def __init__(self, user: User):
        self.user = user

    def list(self, search: str = '', filter: list = []):
        user_story = self.user.stories

        q = Q()
        q.add(Q(title__icontains=search) |
              Q(place__place_name__icontains=search) |
              Q(place__category__icontains=search) |
              Q(tag__icontains=search), q.AND)
        
        if len(filter) > 0:
            query = None
            for element in filter:
                if query is None:
                    query = Q(place__category=element)
                else:
                    query = query | Q(place__category=element)
            q.add(query, q.AND)
        
        stories = user_story.filter(q).annotate(
            place_name=F('place__place_name'),
            category=F('place__category'),
            writer_is_verified=F('writer__is_verified'),
            nickname=F('writer__nickname'),
            # profile=Concat(Value(settings.MEDIA_URL),
            #                F('writer__profile_image'),
            #                output_field=CharField()),
            extra_pics=GroupConcat('photos__image'),
        ).order_by('-created')

        for story in stories:
            story.rep_pic = story.rep_pic.url
            if story.extra_pics is not None:
                story.extra_pics = map(
                    append_media_url, story.extra_pics.split(',')[:3])

        return stories
        
        