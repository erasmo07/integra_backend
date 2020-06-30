from django.contrib import admin
from . import models

from integrabackend.contrib.admin import display_all


class TypeInvitationProyectAdmin(admin.ModelAdmin):
    list_display = display_all(models.TypeInvitationProyect)


class InvitationAdmin(admin.ModelAdmin):
    list_display = display_all(models.Invitation)



# Register your models here.
admin.site.register(models.TypeInvitation)
admin.site.register(models.TypeInvitationProyect, TypeInvitationProyectAdmin)
admin.site.register(models.Invitation, InvitationAdmin)
admin.site.register(models.CheckIn)
admin.site.register(models.CheckOut)
admin.site.register(models.Terminal)
admin.site.register(models.CheckPoint)
admin.site.register(models.Transportation)
admin.site.register(models.Color)
admin.site.register(models.Medio)