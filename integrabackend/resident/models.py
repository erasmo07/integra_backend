import uuid
from django.db import models


class Resident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    telephone = models.CharField(max_length=12, null=True, blank=True)
    is_active = models.BooleanField(default=False)


class TypeIdentification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    count_character = models.IntegerField()


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    create_by = models.ForeignKey(Resident, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    type_identification = models.ForeignKey(
        TypeIdentification, on_delete=models.CASCADE)
    identification = models.CharField(max_length=30)
    email = models.EmailField()
    depurate = models.BooleanField(default=False)
