import factory
from datetime import datetime
from ...resident.test.factories import ResidentFactory
from ..models import TypeInvitation


class TypeInvitationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'invitation.TypeInvitation'


class InvitationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'invitation.Invitation'

    id = factory.Faker('uuid4')
    date_entry = factory.LazyFunction(datetime.now)
    date_out = factory.LazyFunction(datetime.now)
