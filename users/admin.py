from . import models
from django.contrib import admin

# Register your models here.


@admin.register(models.User)
class CustomUserAdmin(admin.ModelAdmin):
    """"""
    pass
