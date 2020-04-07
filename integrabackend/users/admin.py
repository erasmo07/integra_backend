from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from . import models


@admin.register(models.User)
class UserAdmin(UserAdmin):
    pass


admin.site.register(models.Application)
admin.site.register(models.AccessApplication)
admin.site.register(models.AccessDetail)
admin.site.register(models.Merchant)