from django.urls import reverse
from django.forms.models import model_to_dict
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_

from .factories import (
    ServiceFactory, ServiceRequestFactory, StateFactory,
    DayFactory, DateServiceRequestFactory)
from ...users.test.factories import UserFactory
from integrabackend.resident.test.factories import PropertyFactory, PropertyTypeFactory


faker = Faker()

class TestServiceTestCase(APITestCase):
    """
    Tests /service list.
    """

    def setUp(self):
        self.model = ServiceFactory._meta.model
        self.factory = ServiceFactory
        self.base_name = 'service'
        self.url = reverse('%s-list' % self.base_name)
        self.client.force_authenticate(user=UserFactory.build())

    def test_get_request_list_succeeds(self):
        self.factory.create()
        response = self.client.get(self.url)
        for service in response.json().get('results'):
            ok_(service.get('id'))
            ok_(service.get('name') is not None)

    def test_get_request_with_pk_succeeds(self):
        service = self.factory.create()
        url = reverse(
            '%s-detail' % self.base_name,
            kwargs={'pk': service.id})

        response = self.client.get(url)

        service = response.json()
        ok_(service.get('id'))
        ok_(service.get('name') is not None)


class TestSolicitudeServiceTestCase(APITestCase):
    """
    Test /solicitude-service CRUD
    """

    def setUp(self):
        self.model = ServiceRequestFactory._meta.model 
        self.factory = ServiceRequestFactory
        self.base_name = 'servicerequest'
        self.url = reverse('%s-list' % self.base_name)
        self.client.force_authenticate(user=UserFactory.build())
    
    def test_request_post_success(self):
        property = PropertyFactory(
            property_type=PropertyTypeFactory.create())
        date_service_request = DateServiceRequestFactory()
        date_service_request.day.add(DayFactory.create())
        service_request = ServiceRequestFactory(
            service=ServiceFactory.create(),
            state=StateFactory.create(),
            user=UserFactory.create(), 
            property=property,
            date_service_request=date_service_request)
        data = model_to_dict(service_request)
        data['date_service_request'] = model_to_dict(date_service_request)
        data['date_service_request']['day'] = [DayFactory.create().pk]

        response = self.client.post(self.url, data)

        eq_(response.status_code, status.HTTP_201_CREATED)
        service = response.json()
        ok_(service.get('id'))
        ok_(service.get('creation_date'))
        eq_(service.get('service'), service_request.service.pk)
        eq_(service.get('state'), service_request.state.pk)
        eq_(service.get('note'), service_request.note)
        eq_(service.get('phone'), service_request.phone)
        eq_(service.get('email'), service_request.email)
        eq_(service.get('ownership'), service_request.ownership)


class TestAvisoTestCase(APITestCase):
    """
    Test /aviso endpoint
    """
    def setUp(self):
        self.base_name = 'create_aviso'
        self.url = reverse('%s-list' % self.base_name)
        self.client.force_authenticate(user=UserFactory.build())
        return super(TestAvisoTestCase, self).setUp()
    
    def test_request_post_without_ticket_id(self):
        body = {'ticket_id': ''} 

        response = self.client.post(self.url, data=body)
        eq_(response.status_code, status.HTTP_404_NOT_FOUND)
        eq_(response.content, b'{"message":"Not set ticket_id"}')
    
    def test_request_post_service_request_not_exists(self):
        body = {'ticket_id': 1} 

        response = self.client.post(self.url, data=body)
        eq_(response.status_code, status.HTTP_404_NOT_FOUND)
        eq_(response.content,
            b'{"message":"Not exists service request with it ticket_id"}')
    
    def test_request_get_without_ticket_id(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_404_NOT_FOUND)
        eq_(response.content, b'{"message":"Not set ticket_id"}')       
    
    def test_request_get_service_request_not_exists(self):
        body = {'ticket_id': 1} 

        response = self.client.get(self.url, data=body)
        eq_(response.status_code, status.HTTP_404_NOT_FOUND)
        eq_(response.content,
            b'{"message":"Not exists service request with it ticket_id"}')
    
    def test_request_get_success(self):
        property = PropertyFactory(
            property_type=PropertyTypeFactory.create())
        date_service_request = DateServiceRequestFactory()
        day_type = DayTypeFactory()
        day = DayFactory(day_type=day_type)
        date_service_request.day.add(day)
        service_request = ServiceRequestFactory(
            service=ServiceFactory.create(),
            state=StateFactory.create(),
            user=UserFactory.create(), 
            property=property,
            date_service_request=date_service_request,
            ticket_id=1, aviso_id=1)

        body = {'ticket_id': 1} 
        response = self.client.get(self.url, data=body)
        eq_(response.status_code, status.HTTP_200_OK)
    
    def test_request_patch_success(self):
        property = PropertyFactory(
            property_type=PropertyTypeFactory.create())
        date_service_request = DateServiceRequestFactory()
        day_type = DayTypeFactory()
        day = DayFactory(day_type=day_type)
        date_service_request.day.add(day)
        service_request = ServiceRequestFactory(
            service=ServiceFactory.create(),
            state=StateFactory.create(),
            user=UserFactory.create(), 
            property=property,
            date_service_request=date_service_request,
            ticket_id=1, aviso_id=1)

        body = {'state': 'RACU'} 
        url = reverse("%s-detail" % self.base_name, kwargs={"pk": 1})
        response = self.client.put(url, data=body)

        eq_(response.status_code, status.HTTP_200_OK)
        ok_(response.json().get('success'))
        eq_(len(mail.outbox), 1)