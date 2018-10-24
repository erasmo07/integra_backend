from django.urls import reverse
from django.forms.models import model_to_dict
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_

from ..models import Resident
from ..serializers import ResidentSerializer
from .factories import (
    ResidentFactory, PersonFactory, TypeIdentificationFactory,
    PropertyFactory, PropertyTypeFactory)
from ...users.test.factories import UserFactory


fake = Faker()


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

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        resident = Resident.objects.get(pk=response.data.get('id'))
        eq_(resident.name, self.data.get('name'))
        eq_(resident.email, self.data.get('email'))
        eq_(resident.telephone, self.data.get('telephone'))
        ok_(resident.is_active)

    def test_get_request_with_pk_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        resident = Resident.objects.get(pk=response.data.get('id'))
        url = reverse('%s-detail' % self.base_name, kwargs={'pk': resident.id})
        response = self.client.get(url)
        eq_(resident.name, response.json().get('name'))
        eq_(resident.email, response.json().get('email'))
        eq_(resident.telephone, response.json().get('telephone'))


class TestPersonTestCase(APITestCase):
    """
    Tests /person ENDPOINT operations.
    """

    def setUp(self):
        self.base_name = 'person'
        self.url = reverse('%s-list' % self.base_name)
        self.model = PersonFactory._meta.model
        self.data = model_to_dict(
            PersonFactory(
                create_by=ResidentFactory(user=UserFactory.create()),
                type_identification=TypeIdentificationFactory.create()))
        self.client.force_authenticate(user=UserFactory.build())

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        person = self.model.objects.get(pk=response.data.get('id'))
        eq_(person.name, self.data.get('name'))
        eq_(person.identification, self.data.get('identification'))

        eq_(str(person.create_by.id), self.data.get('create_by'))
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