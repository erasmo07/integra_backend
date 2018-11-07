import uuid
import calendar
import datetime as dt
from django.conf import settings
from django.db import models

day_name = list(calendar.day_name)
CHOICE_DAY = [list(a) for a in zip(day_name, day_name)] 
CHOICE_TIME = [(i, dt.time(i).strftime('%I %p')) for i in range(24)]
CHOICE_TYPE_DATE = [
    ('Laborable', 'Laborable'),
    ('Fin de semana', 'Fin de semana')]


class Service(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField(max_length=60) 
    generates_invoice = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    sap_code_service = models.CharField(max_length=50)

    def __str__(self):
        return self.name 

    def __unicode__(self):
        return self.nane 


class State(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name 


class ServiceRequest(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    sap_customer = models.CharField(max_length=5)
    creation_date = models.DateTimeField(auto_now_add=True)
    close_date = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True)
    phone = models.CharField(max_length=32)
    email = models.EmailField()
    ticket_id = models.IntegerField(null=True)

    service = models.ForeignKey("solicitude.Service", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    state = models.ForeignKey(
        'solicitude.State',
        related_name='state',
        on_delete=models.CASCADE)
    property = models.ForeignKey(
        'resident.Property',
        related_name='property',
        on_delete=models.PROTECT,)
    date_service_request = models.OneToOneField(
        'solicitude.DateServiceRequested',
        on_delete=models.CASCADE)


class DateServiceRequested(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)   
    checking = models.CharField(max_length=2, choices=CHOICE_TIME)
    checkout = models.CharField(max_length=2, choices=CHOICE_TIME)
    day = models.ManyToManyField('solicitude.Day')


class Day(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)   
    name = models.CharField(
        max_length=10, choices=CHOICE_DAY,
        unique=True) 
    active = models.BooleanField(default=True)
    day_type = models.ForeignKey(
        'solicitude.DayType',
        on_delete=models.PROTECT)


class DayType(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField(
        max_length=20, choices=CHOICE_TYPE_DATE)


class ScheduleAvailability(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    day_type = models.OneToOneField(
        'solicitude.DayType',
        on_delete=models.PROTECT,
        related_name='schedule_availability')
    start_time = models.TimeField()
    end_time = models.TimeField()
    msg_display = models.CharField(max_length=50)