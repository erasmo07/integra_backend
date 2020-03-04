import uuid
import random
from django.db import models, IntegrityError


def random_number():
    return str(random.randint(10000, 99999))


class Medio(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField('Name', max_length=50)
    icon = models.CharField('Icon', max_length=50, blank=True, null=True)


class Color(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField('Nombre', max_length=50)


class Transportation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    plate = models.CharField('Plate', max_length=50)
    color = models.ForeignKey(
        "invitation.Color", on_delete=models.CASCADE)
    medio = models.ForeignKey(
        "invitation.Medio", on_delete=models.CASCADE)


class Supplier(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField('Name Suplier', max_length=250)
    transportation = models.ForeignKey(
        "invitation.Transportation", on_delete=models.CASCADE)


class TypeInvitation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField(max_length=120)


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_entry = models.DateTimeField()
    date_out = models.DateTimeField()
    cheking = models.DateTimeField(null=True, blank=True)
    chekout = models.DateTimeField(null=True, blank=True)
    note = models.TextField('Note', blank=True, null=True)
    number = models.CharField(
        'Random Number', max_length=7,
        unique=True, blank=True, null=True)

    create_by = models.ForeignKey(
        'users.User', related_name='invitations',
        on_delete=models.CASCADE)
    type_invitation = models.ForeignKey(
        'invitation.TypeInvitation', related_name='invitations',
        on_delete=models.CASCADE)
    supplier = models.ForeignKey(
        "invitation.Supplier", on_delete=models.SET_NULL,
        blank=True, null=True)

    invitated = models.ManyToManyField('resident.Person')

    def save(self, *args, **kwargs):
        try:
            self.number = random_number()
            super(Invitation, self).save(*args, **kwargs)
        except IntegrityError:
            self.number = random_number()
            return super(Invitation, self).save(*args, **kwargs)
