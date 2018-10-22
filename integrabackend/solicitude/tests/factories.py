import factory
import random

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