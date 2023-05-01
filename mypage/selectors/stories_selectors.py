from django.db.models import F

from users.models import User
from stories.models import Story


class UserStorySelector:
    def __init__(self, user: User):
        self.user = user

    def list(self):
        stories = self.user.stories.filter(
            writer=self.user).order_by('created')

        return stories

    def get_by_comment(self):

        my_story_comments = self.user.story_comments.filter(
            writer=self.user).values_list('story')
        story_filter = [y for x in set(my_story_comments) for y in x]

        stories = Story.objects.filter(id__in=story_filter).annotate(
            place_name=F('address__place_name')
        ).order_by('created')

        return stories
