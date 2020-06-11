import random
from datetime import datetime, timezone

import factory
import factory.fuzzy

from integrabackend.resident.test.factories import PropertyFactory
from integrabackend.users.test.factories import UserFactory

from ...resident.test.factories import ResidentFactory
from ..models import TypeInvitation


class StatusInvitationFactory(factory.django.DjangoModelFactory):
    
    class Meta:
        model = 'invitation.StatusInvitation'


class TypeInvitationFactory(factory.django.DjangoModelFactory):
    name = 'Pending'

    class Meta:
        model = 'invitation.TypeInvitation'


class InvitationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'invitation.Invitation'

    id = factory.Faker('uuid4')
    date_entry = factory.fuzzy.FuzzyDateTime(
        datetime(2008, 1, 1, tzinfo=timezone.utc))
    date_out = factory.fuzzy.FuzzyDateTime(
        datetime(2008, 1, 1, tzinfo=timezone.utc))
    note = int("".join([str(random.randint(1, 9)) for _ in range(5)]))

    create_by = factory.SubFactory(UserFactory)
    type_invitation = factory.SubFactory(TypeInvitationFactory)
    ownership = factory.SubFactory(PropertyFactory)
    status = factory.SubFactory(StatusInvitationFactory)


class ColorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'invitation.Color'


class MedioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'invitation.Medio'


class TransportationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'invitation.Transportation'

    plate = 'A12345678'
    color = factory.SubFactory(ColorFactory)
    medio = factory.SubFactory(MedioFactory)


class SupplierFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'invitation.Supplier'

    id = factory.Faker('uuid4')
    transportation = factory.SubFactory(TransportationFactory)
