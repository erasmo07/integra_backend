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
