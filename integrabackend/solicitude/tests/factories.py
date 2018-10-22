import factory
import random


class ServiceFactory(factory.django.DjangoModelFactory):
    
    class Meta:
        model = 'solicitude.Service'

    id = factory.Faker('uuid4')
    name = factory.Sequence(lambda n: f'testuser{n}')