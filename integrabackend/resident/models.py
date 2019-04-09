import uuid
from django.conf import settings
from django.db import models


class Resident(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)

    name = models.CharField(max_length=120)
    email = models.EmailField()
    identification = models.CharField(max_length=20)
    id_sap = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)
    telephone = models.CharField(max_length=12, null=True, blank=True)
    sap_customer = models.CharField(max_length=10)

    properties = models.ManyToManyField('resident.Property')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)


class TypeIdentification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    count_character = models.IntegerField()


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    create_by = models.ForeignKey('resident.Resident', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    type_identification = models.ForeignKey(
        TypeIdentification, on_delete=models.CASCADE)
    identification = models.CharField(max_length=30)
    email = models.EmailField()
    depurate = models.BooleanField(default=False)


class PropertyType(models.Model):
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name


class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_sap = models.CharField(max_length=10)
    name = models.CharField(max_length=64)
    property_type = models.ForeignKey(
        'resident.PropertyType', on_delete=models.PROTECT)
    address = models.CharField(max_length=128)
    street = models.CharField(max_length=64)
    number = models.CharField(max_length=5)
    project = models.ForeignKey(
        "resident.Project", on_delete=models.CASCADE, null=True)

    @property
    def direction(self):
        return f'{self.address}'


class Department(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField(max_length=64)
    email = models.EmailField()
    fave_id = models.IntegerField()

    def __str__(self):
        return self.name


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_sap = models.CharField(max_length=10)
    name = models.CharField(max_length=64)
    area = models.ForeignKey('resident.Area', on_delete=models.PROTECT)
    department = models.ForeignKey(
        "resident.Department", on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.name


class ProjectService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey("resident.Project", on_delete=models.CASCADE)
    services = models.ManyToManyField("solicitude.Service")


class Area(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_sap = models.CharField(max_length=10)
    name = models.CharField(max_length=64)
    organization = models.ForeignKey('resident.Organization', on_delete=models.PROTECT)


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
