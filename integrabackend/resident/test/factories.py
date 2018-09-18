import factory


class ResidentFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'resident.Resident'

    id = factory.Faker('uuid4')
    name = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    telephone = 'telephone'
    is_active = True
