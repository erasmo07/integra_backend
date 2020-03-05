from django.contrib import admin
from . import models


def display_all(model):
    """ Function to list all element of one model. """
    return [field.name for field in model._meta.fields
            if field.name != "id"]


class TypeInvitationProyectAdmin(admin.ModelAdmin):
    list_display = display_all(models.TypeInvitationProyect)


# Register your models here.
admin.site.register(models.TypeInvitation)
admin.site.register(models.TypeInvitationProyect, TypeInvitationProyectAdmin)