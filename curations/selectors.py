# from django.db.models import Q, F
# from users.models import
from curations.models import Curation
from users.models import User
from stories.models import Story

from django.conf import settings
from django.db.models.functions import Concat, Substr
from django.db.models import Q, F, Case, When, Value, Exists, OuterRef, CharField


class CurationSelector:
    def __init__(self, user: User):
        self.user = user

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
            writer_is_verified=F('writer__is_verified')
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
        )

        return curations

    def admin_curation_list(self):
        curations = Curation.objects.filter(
            is_released=True, writer__is_sdp_admin=True, is_rep=False).annotate(
            rep_pic=Case(
                When(
                    photos__image=None,
                    then=None
                ),
                default=Concat(Value(settings.MEDIA_URL),
                               F('photos__image'),
                               output_field=CharField())
            ),
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
        curated_stories = CuratedStorySelector.detail(
            story_id_list=story_id_list, user=self.user)

        return curated_stories


class CuratedStorySelector:
    def __init__(self):
        pass

    def detail(story_id_list: list, user: User):
        return Story.objects.filter(id__in=story_id_list).values('id', 'story_review', 'tag', 'story_likeuser_set').annotate(
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
            )
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
