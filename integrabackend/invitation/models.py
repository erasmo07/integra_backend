import uuid
from django.db import models

# Create your models here.


class TypeInvitation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    name = models.CharField(max_length=120)


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    create_by = models.ForeignKey(
        'users.User', related_name='invitations',
        on_delete=models.CASCADE)
    type_invitation = models.ForeignKey(
        'invitation.TypeInvitation', related_name='invitations',
        on_delete=models.CASCADE)
    note = models.TextField('Note', blank=True, null=True)
    invitated = models.ManyToManyField('resident.Person')
    date_entry = models.DateTimeField()
    date_out = models.DateTimeField()
    cheking = models.DateTimeField(null=True, blank=True)
    chekout = models.DateTimeField(null=True, blank=True)
