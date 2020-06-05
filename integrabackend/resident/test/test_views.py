import random

from django.forms.models import model_to_dict
from django.urls import reverse
from nose.tools import eq_, ok_
from rest_framework import status
from rest_framework.test import APITestCase

from ...users.enums import GroupsEnums
from ...users.test.factories import (AccessApplicationFactory,
                                     ApplicationFactory, UserFactory)
from ..models import Resident
from ..serializers import ResidentSerializer
from . import factories
from .factories import (AreaFactory, PersonFactory, PropertyFactory,
                        PropertyTypeFactory, ResidentFactory,
                        TypeIdentificationFactory)


class TestResidentListTestCase(APITestCase):
    """
    Tests /resident list operations.
    """

    def setUp(self):
        self.base_name = 'resident'
        self.url = reverse('%s-list' % self.base_name)
        self.data = ResidentSerializer(
            ResidentFactory(user=UserFactory.create())).data
        self.client.force_authenticate(user=UserFactory.create())

        self.application = ApplicationFactory.create(
            name='Portal PCIS', merchant__name='PCIS',
            merchant__number='0000', domain='domain front')

    def test_get_request_retun_sap_customer_from_access_detail(self):
        # GIVEN
        resident = ResidentFactory.create(user=UserFactory.create())
        access = AccessApplicationFactory.create(user=resident.user)
        access.details.create(sap_customer='test', default=True)

        # WHEN
        self.client.credentials(
            HTTP_APPLICATION=f'Bifrost {access.application.id}')
        response = self.client.get(f'/api/v1/resident/{resident.pk}/')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('test', response.json().get('sap_customer'))

    def test_get_resident_by_sap_customer(self):
        # GIVEN
        for _ in range(10):
            ResidentFactory(user=UserFactory.create())

        resident = ResidentFactory.create(user=UserFactory.create())
        access = AccessApplicationFactory.create(user=resident.user)
        access.details.create(sap_customer='test', default=True)

        # WHEN
        response = self.client.get(self.url, {'sap_customer': 'test'})

        # THEN
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_get_request_with_pk_succeeds(self):
        data = model_to_dict(ResidentFactory(user=UserFactory()))
        Resident.objects.all().delete()
        response = self.client.post(self.url, data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        resident = Resident.objects.get(pk=response.data.get('id'))
        url = reverse('%s-detail' % self.base_name, kwargs={'pk': resident.id})
        response = self.client.get(url)
        eq_(resident.name, response.json().get('name'))
        eq_(resident.email, response.json().get('email'))
        eq_(resident.telephone, response.json().get('telephone'))

    def test_get_request_return_properties(self):
        data = model_to_dict(ResidentFactory(user=UserFactory()))
        Resident.objects.all().delete()
        response = self.client.post(self.url, data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        resident = Resident.objects.get(pk=response.data.get('id'))
        eq_(resident.name, data.get('name'))
        eq_(resident.email, data.get('email'))
        eq_(resident.telephone, data.get('telephone'))

        _property = PropertyFactory(property_type=PropertyTypeFactory.create())
        resident.properties.add(_property)

        url = reverse('%s-detail' % self.base_name, kwargs={'pk': resident.id})
        response = self.client.get(url)

        for _property in response.json().get('properties'):
            ok_(resident.properties.get(pk=_property.get('id')))

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        data = model_to_dict(ResidentFactory(user=UserFactory.create()))
        Resident.objects.all().delete()
        response = self.client.post(self.url, data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        resident = Resident.objects.get(pk=response.data.get('id'))
        eq_(resident.name, data.get('name'))
        eq_(resident.email, data.get('email'))
        eq_(resident.telephone, data.get('telephone'))

    def test_post_request_add_property(self):
        data = model_to_dict(ResidentFactory(user=UserFactory()))
        Resident.objects.all().delete()
        response = self.client.post(self.url, data)
        eq_(response.status_code, status.HTTP_201_CREATED)
        eq_(len(response.json().get('properties')), 0)

        property_object = PropertyFactory(property_type=PropertyTypeFactory())
        property_data = {'properties': [str(property_object.id)]}

        resident = Resident.objects.get(pk=response.data.get('id'))
        url = reverse('%s-detail' % self.base_name, kwargs={'pk': resident.id})
        url_property = url + 'property/'
        response = self.client.post(url_property, property_data)

        eq_(response.status_code, status.HTTP_201_CREATED)
        for _property in response.json():
            eq_(property_object.id_sap, _property.get('id_sap'))
            eq_(property_object.name, _property.get('name'))
            eq_(property_object.address, _property.get('address'))
            eq_(property_object.street, _property.get('street'))
            eq_(property_object.number, _property.get('number'))

        url = reverse('%s-detail' % self.base_name, kwargs={'pk': resident.id})
        resident = self.client.get(url)
        eq_(len(resident.json().get('properties')), 1)

    def test_post_request_add_two_property_at_time(self):
        data = model_to_dict(ResidentFactory(user=UserFactory()))
        Resident.objects.all().delete()
        response = self.client.post(self.url, data)
        eq_(response.status_code, status.HTTP_201_CREATED)
        eq_(len(response.json().get('properties')), 0)

        property_one = PropertyFactory(property_type=PropertyTypeFactory())
        property_two = PropertyFactory(property_type=PropertyTypeFactory())
        property_data = {'properties': [
            str(property_one.id), str(property_two.id)]
        }

        resident = Resident.objects.get(pk=response.data.get('id'))
        url = reverse('%s-detail' % self.base_name, kwargs={'pk': resident.id})
        url_property = url + 'property/'
        response = self.client.post(url_property, property_data)

        eq_(response.status_code, status.HTTP_201_CREATED)

        ok_(resident.properties.filter(
            id__in=[str(property_one.id), str(property_two.id)]).exists())
        eq_(resident.properties.filter(
            id__in=[str(property_one.id), str(property_two.id)]).count(), 2)

        url = reverse('%s-detail' % self.base_name, kwargs={'pk': resident.id})
        resident = self.client.get(url)
        eq_(len(resident.json().get('properties')), 2)

    def test_post_request_add_user(self):
        resident_data = model_to_dict(ResidentFactory())

        Resident.objects.all().delete()
        resident_data.pop('user')
        response = self.client.post(self.url, resident_data)

        eq_(response.status_code, status.HTTP_201_CREATED)
        eq_(len(response.json().get('properties')), 0)

        user = UserFactory()
        user_data = model_to_dict(user, exclude=['id'])
        user.delete()

        resident = Resident.objects.get(pk=response.data.get('id'))

        url = reverse('%s-detail' % self.base_name, kwargs={'pk': resident.id})
        response = self.client.post(url + 'user/', user_data)

        eq_(response.status_code, status.HTTP_201_CREATED)

    def test_user_normal_cant_assign_access(self):
        # GIVE
        user = UserFactory.create()
        resident = ResidentFactory(user=user)
        self.client.force_authenticate(user=user)

        # WHEN
        url_detail = reverse(
            '%s-detail' % self.base_name,
            kwargs={'pk': resident.id})
        url = f'{url_detail}access/'
        response = self.client.post(
            url,
            {"applications": [str(self.application.id)]})

        # THEN
        self.assertEqual(response.status_code, 403)

    def test_user_backoffice_cant_assign_access(self):

        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.backoffice)
        self.client.force_authenticate(user=user)

        # WHEN
        resident = ResidentFactory(user=UserFactory.create())
        url_detail = reverse(
            '%s-detail' % self.base_name,
            kwargs={'pk': resident.id})
        url = f'{url_detail}access/'
        response = self.client.post(
            url,
            {"applications": [str(self.application.id)]})

        # THEN
        self.assertEqual(response.status_code, 403)

    def test_application_not_exists(self):
        # GIVEN
        resident = ResidentFactory()
        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.application)
        self.client.force_authenticate(user=user)

        # WHEN
        url_detail = reverse(
            '%s-detail' % self.base_name,
            kwargs={'pk': resident.id})
        url = f'{url_detail}access/'
        body = {"applications": [str(self.application.id)]}
        self.application.delete()
        response = self.client.post(url, body)

        # THEN
        self.assertEqual(response.status_code, 400)

    def test_user_application_can_assing_access(self):
        # GIVEN
        resident = ResidentFactory(user=UserFactory.create())
        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.application)

        self.client.force_authenticate(user=user)

        # WHEN
        url_detail = reverse(
            '%s-detail' % self.base_name,
            kwargs={'pk': resident.id})
        url = f'{url_detail}access/'
        body = {
            "application": self.application.id,
            "details": [{'sap_customer': 'prueba', 'default': False}]
        }
        response = self.client.post(url, body, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(resident.user.accessapplication_set.filter(
            application_id=self.application.id).exists())


class TestPersonTestCase(APITestCase):
    """
    Tests /person ENDPOINT operations.
    """

    def setUp(self):
        self.base_name = 'person'
        self.url = reverse('%s-list' % self.base_name)
        self.model = PersonFactory._meta.model
        self.data = model_to_dict(PersonFactory.create())
        self.user = UserFactory.create()
        self.client.force_authenticate(user=self.user)

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        person = self.model.objects.get(pk=response.data.get('id'))
        eq_(person.name, self.data.get('name'))
        eq_(person.identification, self.data.get('identification'))

        eq_(str(person.create_by.id), str(self.user.id))
        eq_(str(person.type_identification.id),
            str(self.data.get('type_identification')))


class TestPropertyTestCase(APITestCase):
    """
    Tests /property ENDPOINT operations
    """

    def setUp(self):
        self.base_name = 'property'
        self.url = reverse('%s-list' % self.base_name)
        self.model = PropertyFactory._meta.model
        self.data = model_to_dict(PropertyFactory(
            property_type=PropertyTypeFactory.create()))
        self.client.force_authenticate(user=UserFactory.create())

    def test_get_request_without_pk(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)


class TestDeparment(APITestCase):

    def setUp(self):
        self.url = '/api/v1/department/'
        self.factory = factories.DepartmentFactory

        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.application)
        self.client.force_login(user=user)

    def test_backoffice_cant_list(self):
        # GIVEN
        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.backoffice)
        self.client.force_login(user=user)

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_list_departments(self):
        # GIVEN
        for _ in range(5):
            self.factory.create()

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 5)

        for department in response.json():
            self.assertIn('id', department)
            self.assertIn('name', department)

    def test_cant_create_department(self):
        # GIVEN
        data = model_to_dict(self.factory.create(), exclude=['id'])

        # WHEN
        response = self.client.post(self.url, data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TestOrganization(APITestCase):

    def setUp(self):
        self.url = '/api/v1/organization/'
        self.factory = factories.OrganizationFactory

        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.application)
        self.client.force_login(user=user)

    def test_backoffice_cant_list(self):
        # GIVEN
        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.backoffice)
        self.client.force_login(user=user)

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_list_organization(self):
        # GIVEN
        for _ in range(5):
            self.factory.create()

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 5)

        for department in response.json():
            self.assertIn('id', department)
            self.assertIn('name', department)

    def test_cant_create_organization(self):
        # GIVEN
        data = model_to_dict(self.factory.create(), exclude=['id'])

        # WHEN
        response = self.client.post(self.url, data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TestArea(APITestCase):

    def setUp(self):
        self.url_to_add = '/api/v1/area/'
        self.url_to_list = '/api/v1/area/'

        self.model = factories.AreaFactory._meta.model
        self.field_validate = ['id', 'name']
        self.factory = factories.AreaFactory

        user = UserFactory()
        user.groups.create(name=GroupsEnums.application)

        self.client.force_login(user=user)

    def test_get_request(self):
        for _ in range(5):
            self.factory.create()

        response = self.client.get(self.url_to_list)

        self.assertEqual(len(response.json()), 5)

    def test_post_request_success_data(self):
        data = model_to_dict(
            self.factory.create(), exclude=['id'])

        response = self.client.post(self.url_to_add, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.model.objects.count(), 2)

        instance = self.model.objects.get(id=response.json().get('id'))
        self.assertEqual(getattr(instance, 'name'), data.get('name'))

    def test_post_with_update_data_success(self):
        instance = self.factory.create()
        data = model_to_dict(self.factory.create())

        url = '{}{}/'.format(self.url_to_add, instance.pk)
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.model.objects.count(), 2)

        instance.refresh_from_db()

        self.assertEqual(getattr(instance, 'name'), data.get('name'))


class TestProyect(APITestCase):

    def setUp(self):
        self.url = '/api/v1/project/'
        self.factory = factories.ProjectFactory
        self.model = self.factory._meta.model

        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.application)
        self.client.force_login(user=user)

    def test_can_list_projects(self):
        # GIVEN
        for _ in range(5):
            self.factory.create()

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 5)

    def test_cant_normal_user_create_project(self):
        # GIVEN
        self.client.force_login(user=UserFactory.create())
        data = model_to_dict(self.factory.create(), exclude=[''])

        # WHEN
        response = self.client.post(self.url, data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_backoffice_create_project(self):
        # GIVEN
        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.backoffice)
        self.client.force_login(user=user)

        # WHEN
        data = model_to_dict(self.factory.create(), exclude=[''])
        response = self.client.post(self.url, data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_create_project(self):
        # GIVEN
        data = model_to_dict(self.factory.create(), exclude=[''])

        # WHEN
        response = self.client.post(self.url, data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        instance = self.model.objects.get(id=response.json().get('id'))

    def test_can_update_project(self):
        # GIVEN
        project = self.factory.create()

        data = model_to_dict(self.factory.create(), exclude=[''])

        # WHEN
        response = self.client.put(f'{self.url}{project.id}/', data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        project.refresh_from_db()

        self.assertEqual(project.id_sap, data.get('id_sap'))
        self.assertEqual(project.name, data.get('name'))

        self.assertEqual(project.area.id, data.get('area'))
        self.assertEqual(project.department.id, data.get('department'))
