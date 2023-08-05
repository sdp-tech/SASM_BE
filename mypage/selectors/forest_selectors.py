from django.db.models import F, Q, Aggregate, CharField
from django.conf import settings

from users.models import User
from forest.models import Forest

class UserForestSelector:
    def __init__(self, user: User):
        self.user = user

    def list(self, search: str = '', category_filter: list = []):
        like_forest = self.user.liked_forests.all()

        q = Q()
        q.add(Q(title__icontains=search) |
              Q(subtitle__icontains=search) |
              Q(content__icontains=search) |
              Q(hashtags__name__icontains=search), q.AND)
        
        if len(category_filter) > 0:
            query = None
            for element in category_filter:
                if query is None:
                    query = Q(category=element)
                else:
                    query = query | Q(category=element)
            q.add(query, q.AND)

        forests = like_forest.filter(q).annotate(
            writer_is_verified=F('writer__is_verified'),
        ).order_by('-created').prefetch_related('hashtags').distinct()

        return forests
    
    
class UserCreatedForestSelector:
    def __init__(self, user: User):
        self.user = user

    def list(self, search: str, category_filter: list = []):
        user_forest = self.user.forests

        q = Q()
        q.add(Q(title__icontains=search) |
              Q(subtitle__icontains=search) |
              Q(content__icontains=search) |
              Q(hashtags__name__icontains=search), q.AND)
        
        if len(category_filter) > 0:
            query = None
            for element in category_filter:
                if query is None:
                    query = Q(category=element)
                else:
                    query = query | Q(category=element)
            q.add(query, q.AND)

        forests = user_forest.filter(q).annotate(
            writer_is_verified=F('writer__is_verified'),
        ).order_by('-created').prefetch_related('hashtags').distinct()

        return forests