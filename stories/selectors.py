from datetime import datetime
from dataclasses import dataclass
from collections import Counter
from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Aggregate, Value, CharField, Case, When
from django.db.models.functions import Concat, Substr
from users.models import User
from stories.models import Story, StoryPhoto, StoryComment


class StoryCommentSelector:
    def __init__(self):
        pass

    def isWriter(self, story_comment_id: int, user: User):
        return StoryComment.objects.get(id=story_comment_id).writer == user