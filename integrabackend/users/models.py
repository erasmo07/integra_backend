import uuid
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
from django.utils.encoding import python_2_unicode_compatible
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token

from . import enums

@python_2_unicode_compatible
class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    email =models.EmailField(unique=True)

    def __str__(self):
        return self.username
    
    @property
    def is_aplication(self):
        return self.groups.filter(
            name=enums.GroupsEnums.application
        ).exists()
    
    @property
    def is_backoffice(self):
        return self.groups.filter(
            name=enums.GroupsEnums.backoffice
        ).exists()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Merchant(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField('Nombre', max_length=50)
    number = models.CharField('Numero', max_length=50)


class Application(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4, editable=False
    )
    name = models.CharField('Nombre', max_length=50, unique=True)
    description = models.TextField('Descripción')
    merchant = models.ForeignKey("users.Merchant", on_delete=models.CASCADE)
    domain = models.CharField('Domain', max_length=250)


class AccessApplication(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    application = models.ForeignKey("users.Application", on_delete=models.CASCADE)
    details = models.ManyToManyField("users.AccessDetail")


class AccessDetail(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    sap_customer = models.CharField(
        'Numero de cliente sap',
        max_length=50, unique=True)
    default = models.BooleanField(default=False)