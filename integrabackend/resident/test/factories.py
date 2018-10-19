import factory
import random


class ResidentFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'resident.Resident'

    id = factory.Faker('uuid4')
    name = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    telephone = 'telephone'
    is_active = True


class TypeIdentificationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'resident.TypeIdentification'

    count_character = random.randrange(0, 256)


class PersonFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'resident.Person'

    name = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    identification = factory.Sequence(lambda n: f'testuser{n}')
