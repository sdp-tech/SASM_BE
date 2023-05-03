from django.db import models
from core import models as core_models
from django.core.exceptions import ValidationError
from django.dispatch import receiver


def get_upload_path(instance, filename):
    return 'curations/{}'.format(filename)


class CurationPhoto(core_models.TimeStampedModel):
    curation = models.ForeignKey(
        "Curation", related_name='photos', on_delete=models.CASCADE, null=True)
    image = models.ImageField(
        upload_to=get_upload_path, default='curation_image.png')


@receiver(models.signals.post_delete, sender=CurationPhoto)
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.image.delete(save=False)


class Curation(core_models.TimeStampedModel):
    title = models.CharField(max_length=100)
    contents = models.CharField(max_length=200, default='')
    story = models.ManyToManyField(
        'stories.Story', through='Curation_Story', related_name='curations')

    likeuser_set = models.ManyToManyField(
        "users.User", related_name='liked_curations', blank=True)
    writer = models.ForeignKey(
        'users.User', related_name='curations', on_delete=models.SET_NULL, null=True, blank=False)

    is_released = models.BooleanField(
        null=False, blank=False, default=False)  # 공개/심사중
    is_selected = models.BooleanField(
        null=False, blank=False, default=False)  # 홈 화면에 보여줄 큐레이션
    is_rep = models.BooleanField(
        null=False, blank=False, default=False)  # 홈 화면 대표 큐레이션

    def update_title(self, title):
        self.title = title

    def update_contents(self, contents):
        self.contents = contents

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Curation_Story(core_models.TimeStampedModel):
    curation = models.ForeignKey(
        'Curation', on_delete=models.CASCADE, related_name='short_curations')
    story = models.ForeignKey(
        'stories.Story', on_delete=models.CASCADE, related_name='short_curations')
    short_curation = models.CharField(max_length=200)

    class Meta:
        db_table = 'curation_story'

    def update_short_curation(self, short_curation):
        self.short_curation = short_curation

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CurationMap(core_models.TimeStampedModel):
    curation = models.ForeignKey(
        "Curation", related_name='map_photos', on_delete=models.CASCADE, null=True)
    map = models.ImageField(
        upload_to=get_upload_path, default='curation_map_photo.png')


@receiver(models.signals.post_delete, sender=CurationMap)
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.map.delete(save=False)
