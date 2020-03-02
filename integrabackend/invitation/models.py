import uuid
import random
from django.db import models, IntegrityError


def random_number():
    return str(random.randint(10000, 99999))


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
    number = models.CharField(
        'Random Number', max_length=7,
        unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            self.number = random_number()
            super(Invitation, self).save(*args, **kwargs)
        except IntegrityError:
            self.number = random_number()
            return super(Invitation, self).save(*args, **kwargs)
