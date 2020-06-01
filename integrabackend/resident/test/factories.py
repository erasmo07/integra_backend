import factory
import random
from integrabackend.users.test.factories import UserFactory


class ResidentFactory(factory.django.DjangoModelFactory):
    
    class Meta:
        model = 'resident.Resident'

    id = factory.Faker('uuid4')
    name = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    telephone = 'telephone'
    is_active = True
    id_sap = factory.Sequence(lambda n: f'0000000{n}')
    sap_customer = factory.Sequence(lambda n: f'0000000{n}')


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
    type_identification = factory.SubFactory(TypeIdentificationFactory)

    create_by = factory.SubFactory(UserFactory)


class PropertyTypeFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'testuser{n}')

    class Meta:
        model = 'resident.PropertyType'


class OrganizationFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    telephone = 'telephone'

    class Meta:
        model = 'resident.Organization'


class AreaFactory(factory.django.DjangoModelFactory):
    id_sap = "".join([str(random.randint(1, 9)) for _ in range(10)]) 
    name = factory.Sequence(lambda n: f'testuser{n}')
    organization = factory.SubFactory(OrganizationFactory)
    
    class Meta:
        model = 'resident.Area'


class DepartmentFactory(factory.django.DjangoModelFactory):
    email = factory.Faker('email')
    name = 'Informatica y Comunicaciones' 
    fave_id = 1 
    
    class Meta:
        model = 'resident.Department'


class ProjectFactory(factory.django.DjangoModelFactory):
    id_sap = "".join([str(random.randint(1, 9)) for _ in range(10)]) 
    name = factory.Sequence(lambda n: f'testuser{n}')
    area = factory.SubFactory(AreaFactory)
    department = factory.SubFactory(DepartmentFactory)
    
    class Meta:
        model = 'resident.Project'


class ProjectServiceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'resident.ProjectService'


class OrganizationFactory(factory.django.DjangoModelFactory):
    
    class Meta:
        model = 'resident.Organization'


class PropertyFactory(factory.django.DjangoModelFactory):
    id_sap = "".join([str(random.randint(1, 9)) for _ in range(10)]) 
    name = factory.Sequence(lambda n: f'testuser{n}')
    address = factory.Sequence(lambda n: f'address {n}')
    street = factory.Sequence(lambda n: f'street {n}')
    number = "".join([str(random.randint(1, 9)) for _ in range(5)]) 
    property_type = factory.SubFactory(PropertyTypeFactory) 
    project = factory.SubFactory(ProjectFactory)

    class Meta:
        model = 'resident.Property'