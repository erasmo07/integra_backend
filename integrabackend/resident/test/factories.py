import factory
import random
from faker import Faker
from integrabackend.users.test.factories import UserFactory


fake = Faker()


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
    name = factory.Sequence(lambda n: f'testuser{n}')


class PersonFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'resident.Person'

    name = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    identification = factory.Sequence(lambda n: f'testuser{n}')
    create_by = ResidentFactory.build()
    type_identification = TypeIdentificationFactory.build()


class PropertyTypeFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'testuser{n}')

    class Meta:
        model = 'resident.PropertyType'


class PropertyFactory(factory.django.DjangoModelFactory):
    id_sap = "".join([str(random.randint(1, 9)) for _ in range(10)]) 
    name = factory.Sequence(lambda n: f'testuser{n}')
    address = factory.Sequence(lambda n: f'testuser{n}')
    street = factory.Sequence(lambda n: f'testuser{n}')
    number = "".join([str(random.randint(1, 9)) for _ in range(5)]) 

    class Meta:
        model = 'resident.Property'
    