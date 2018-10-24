import uuid
from django.conf import settings
from django.db import models


class Service(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField(max_length=60) 
    generates_invoice = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    service = models.ForeignKey("solicitude.Service", on_delete=models.CASCADE)
    state = models.ForeignKey(
        'solicitude.State',
        related_name='state',
        on_delete=models.CASCADE)
    client_sap = models.CharField(max_length=5)
    note = models.TextField()
    creation_date = models.DateTimeField(auto_now_add=True)
    close_date = models.DateTimeField(null=True, blank=True)
    phone = models.CharField(max_length=32)
    property = models.ForeignKey(
        'resident.Property',
        related_name='property',
        on_delete=models.PROTECT,)
    email = models.EmailField()
    ownership = models.CharField(max_length=120)
    ticket_id = models.IntegerField(null=True)