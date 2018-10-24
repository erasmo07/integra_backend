import factory
import random
import calendar
from ..models import CHOICE_DAY, CHOICE_TIME


class StateFactory(factory.django.DjangoModelFactory):
    id = factory.Faker('uuid4')
    name = factory.Sequence(lambda n: f'testuser{n}')

    class Meta:
        model = 'solicitude.State'


class ServiceFactory(factory.django.DjangoModelFactory):
    
    class Meta:
        model = 'solicitude.Service'

    id = factory.Faker('uuid4')
    name = "Desbloqueo de Usuario"


class ServiceRequestFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'solicitude.ServiceRequest'
    
    id = factory.Faker('uuid4')
    note = factory.Sequence(lambda n: f'note{n}')
    client_sap = factory.Sequence(lambda n: f'note{n}')
    ticket_id = factory.Sequence(lambda n: n)
    phone = factory.Sequence(lambda n: f'note{n}')
    phone = factory.Sequence(lambda n: f'{n}@example.com')
    ownership = factory.Sequence(lambda n: f'{n}@example.com')
    email = factory.Sequence(lambda n: f'{n}@example.com')


class DateServiceRequestFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'solicitude.DateServiceRequested'
    
    id = factory.Faker('uuid4')
    checking = factory.Iterator([i for i in range(24)])
    checkout = factory.Iterator([i for i in range(24)])


class DayFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'solicitude.Day'
    
    id = factory.Faker('uuid4')
    name = factory.Iterator(list(calendar.day_name))