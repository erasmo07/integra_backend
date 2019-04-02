from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.ScheduleAvailability)
admin.site.register(models.Service)
admin.site.register(models.Day)
admin.site.register(models.DayType)
admin.site.register(models.ServiceRequest)
admin.site.register(models.Quotation)
