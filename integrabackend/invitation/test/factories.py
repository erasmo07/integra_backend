import random
from datetime import datetime, timezone, date

import factory
import factory.fuzzy

from integrabackend.resident.test.factories import PropertyFactory
from integrabackend.users.test.factories import UserFactory

from ...resident.test.factories import ResidentFactory, PersonFactory
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
    date_entry = factory.fuzzy.FuzzyDate(date(2008, 1, 1))
    date_out = factory.fuzzy.FuzzyDate(date(2008, 1, 1))
    note = int("".join([str(random.randint(1, 9)) for _ in range(5)]))

    create_by = factory.SubFactory(UserFactory)
    type_invitation = factory.SubFactory(TypeInvitationFactory)
    ownership = factory.SubFactory(PropertyFactory)
    status = factory.SubFactory(StatusInvitationFactory)
    invitated = factory.SubFactory(PersonFactory)


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


class CheckPointFactory(factory.django.DjangoModelFactory):
    name = int("".join([str(random.randint(1, 9)) for _ in range(5)]))
    description = int("".join([str(random.randint(1, 9)) for _ in range(5)]))
    address = int("".join([str(random.randint(1, 9)) for _ in range(5)]))

    class Meta:
        model = 'invitation.CheckPoint'


class TerminalFactory(factory.django.DjangoModelFactory):
    name = int("".join([str(random.randint(1, 9)) for _ in range(5)]))
    ip_address = factory.Sequence(lambda n: f'127.0.0.{n}')
    check_point = factory.SubFactory(CheckPointFactory)


    class Meta:
        model = 'invitation.Terminal'


class CheckInFactory(factory.django.DjangoModelFactory):
    guest = factory.SubFactory(PersonFactory)
    transport = factory.SubFactory(TransportationFactory)
    note = int("".join([str(random.randint(1, 9)) for _ in range(5)]))
    total_companions = 2

    user = factory.SubFactory(UserFactory)
    terminal = factory.SubFactory(TerminalFactory)

    class Meta:
        model = 'invitation.CheckIn'


class SupplierFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'invitation.Supplier'

    id = factory.Faker('uuid4')
    transportation = factory.SubFactory(TransportationFactory)
