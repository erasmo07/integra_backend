from django.urls import reverse
from django.forms.models import model_to_dict
from rest_framework import status
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_

from ..models import Resident
from ..serializers import ResidentSerializer
from .factories import (
    ResidentFactory, PersonFactory, TypeIdentificationFactory,
    PropertyFactory, PropertyTypeFactory)
from ...users.test.factories import UserFactory


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
        data = model_to_dict(ResidentFactory(user=UserFactory.create()))
        Resident.objects.all().delete()
        response = self.client.post(self.url, data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        resident = Resident.objects.get(pk=response.data.get('id'))
        eq_(resident.name, data.get('name'))
        eq_(resident.email, data.get('email'))
        eq_(resident.telephone, data.get('telephone'))

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
                create_by=UserFactory.create(),
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