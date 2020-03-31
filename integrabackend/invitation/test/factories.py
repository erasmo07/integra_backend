import factory
import factory.fuzzy
from datetime import datetime, timezone
from ...resident.test.factories import ResidentFactory
from ..models import TypeInvitation


class TypeInvitationFactory(factory.django.DjangoModelFactory):

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

