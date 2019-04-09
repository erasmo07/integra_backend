from django.contrib import admin
from . import models


class ProjectServiceAdmin(admin.ModelAdmin):
    filter_horizontal = ('services',)


# Register your models here.
admin.site.register(models.Property)
admin.site.register(models.PropertyType)
admin.site.register(models.Project)
admin.site.register(models.ProjectService, ProjectServiceAdmin)

admin.site.register(models.Resident)
admin.site.register(models.Area)
admin.site.register(models.Department)
admin.site.register(models.Organization)
