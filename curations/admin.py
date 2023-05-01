from django.contrib import admin
from . import models


@admin.register(models.CurationPhoto)
class CurationPhoto(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.Curation)
class Curation(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.Curation_Story)
class Curation_Story(admin.ModelAdmin):

    """ """

    pass


@admin.register(models.CurationMap)
class CurationMap(admin.ModelAdmin):

    """ """

    pass
