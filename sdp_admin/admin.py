from django.contrib import admin
from . import models


@admin.register(models.Voc)
class VocAdmin(admin.ModelAdmin):
    pass
