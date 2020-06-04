import factory
from django.contrib.auth.models import Group
from .. import models


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: "Group #%s" % n)


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'users.User'
        django_get_or_create = ('username',)

    id = factory.Faker('uuid4')
    username = factory.Sequence(lambda n: f'testuser{n}')
    password = factory.Faker('password', length=10, special_chars=True, digits=True,
                             upper_case=True, lower_case=True)
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False


class MerchantFactory(factory.django.DjangoModelFactory):
    name = 'Name'
    number = 'Number'
    
    class Meta:
        model = models.Merchant


class ApplicationFactory(factory.django.DjangoModelFactory):
    description = 'Description'
    name = factory.Sequence(lambda n: f'testuser{n}')
    merchant = factory.SubFactory(MerchantFactory)
    
    class Meta:
        model = models.Application


class AccessApplicationFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    application = factory.SubFactory(ApplicationFactory)
    
    class Meta:
        model = models.AccessApplication