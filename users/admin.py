from . import models
from django.contrib import admin

# Register your models here.


@admin.register(models.User)
class CustomUserAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    """"""
    pass
=======
    """Custom User Admin"""
    
>>>>>>> ee88f75d1de41bc9065d60a203c33bfbe2d463a3
