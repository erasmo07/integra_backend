import uuid
from django.db import models


class Resident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    telephone = models.CharField(max_length=12, null=True, blank=True)
    is_active = models.BooleanField(default=False)
