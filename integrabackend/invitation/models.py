import uuid
import random
from django.db import models, IntegrityError
from integrabackend.payment.models import Status

from . import enums


def random_number():
    return str(random.randint(100000000000, 999999999999))


class StatusInvitation(Status):
    pass


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
    plate = models.CharField(
        'Plate', max_length=50,
        blank=True, null=True)
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

    def __str__(self):
        return self.name
    
    @property
    def available_days(self):
        return self.typeinvitationproyect.available_days
    
    @property
    def not_available_days(self):
        return self.typeinvitationproyect.not_available_days.all()


class TypeInvitationProyect(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False)
    type_invitation = models.ForeignKey(
        "invitation.TypeInvitation", on_delete=models.CASCADE)
    project = models.ForeignKey(
        "resident.Project", on_delete=models.CASCADE)
    available_days = models.IntegerField('Available Days')
    not_available_days = models.ManyToManyField(
        "solicitude.Day",
        related_name='type_invitation_not_available_day')


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_entry = models.DateField()
    date_out = models.DateField()
    cheking = models.DateTimeField(null=True, blank=True)
    chekout = models.DateTimeField(null=True, blank=True)
    note = models.TextField('Note', blank=True, null=True)
    barcode = models.ImageField(upload_to='invitation-barcode', blank=True, null=True)
    number = models.CharField(
        'Random Number', max_length=12,
        unique=True, blank=True, null=True)

    status = models.ForeignKey(
        "invitation.StatusInvitation", on_delete=models.CASCADE)
    create_by = models.ForeignKey(
        'users.User', related_name='invitations',
        on_delete=models.CASCADE)
    type_invitation = models.ForeignKey(
        'invitation.TypeInvitation', related_name='invitations',
        on_delete=models.CASCADE)
    supplier = models.ForeignKey(
        "invitation.Supplier", on_delete=models.SET_NULL,
        blank=True, null=True)
    ownership = models.ForeignKey(
        "resident.Property",
        on_delete=models.CASCADE)

    invitated = models.ForeignKey("resident.Person", on_delete=models.CASCADE)
    total_companions = models.IntegerField(null=True, blank=True, default=0)

    @property
    def is_pending(self):
        return self.status.name == enums.StatusInvitationEnums.pending
    
    @property
    def is_family_and_friend(self):
        return (
            self.type_invitation.name == 
            enums.TypeInvitationEnums.friend_and_family)

    @property
    def is_supplier(self):
        return (
            self.type_invitation.name == 
            enums.TypeInvitationEnums.supplier)

    property
    def area(self):
        return f'{self.ownership.project.area.name}'

    class Meta:
        permissions = [
            ('can_check_in', 'Puede hacer check-in'),
            ('can_check_out', 'Puede hacer check-out'),
        ]

    def save(self, *args, **kwargs):
        if not self.number:
            number = str(random.randint(100000000000, 999999999999))
            exist_invitation = self._meta.model.objects.filter(number=number)

            if exist_invitation.exists():
                return self.save(*args, **kwargs)
            self.number = number
        super(Invitation, self).save(*args, **kwargs)


class CheckPoint(models.Model):
    """Model definition for CheckPoint."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4, editable=False)
    name = models.CharField('Nombre', max_length=250)
    description = models.TextField('Descripción')
    address = models.CharField('Dirección', max_length=550)

    type_invitation_allowed = models.ManyToManyField(
        "invitation.TypeInvitation")
    areas = models.ManyToManyField("resident.Area")

    def __str__(self):
        """Unicode representation of CheckPoint."""
        return f'{self.name}'


class Terminal(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4, editable=False)
    name = models.CharField('Nombre', max_length=250)
    ip_address = models.GenericIPAddressField(unique=True)
    is_active = models.BooleanField(default=True)

    check_point = models.ForeignKey(
        "invitation.CheckPoint",
        on_delete=models.DO_NOTHING)


class CheckIn(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4, editable=False)
    note = models.CharField(
        'Nota', max_length=50, blank=True, null=True)
    total_companions = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey("users.User", on_delete=models.DO_NOTHING)
    terminal = models.ForeignKey("invitation.Terminal", on_delete=models.DO_NOTHING)

    invitation = models.OneToOneField(
        "invitation.Invitation", on_delete=models.CASCADE)
    guest = models.ForeignKey(
        "resident.Person",
        on_delete=models.DO_NOTHING,
        related_name='check_in_guest')
    persons = models.ManyToManyField(
        "resident.Person",
        related_name='check_in_persons')
    transport = models.ForeignKey(
        "invitation.Transportation", on_delete=models.DO_NOTHING)
    