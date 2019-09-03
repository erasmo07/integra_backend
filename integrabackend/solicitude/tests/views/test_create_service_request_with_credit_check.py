# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_
from django.urls import reverse
from django.test import tag
from django.forms.models import model_to_dict
from rest_framework import status
from ....users.test.factories import UserFactory
from ..factories import (
    ServiceFactory, ServiceRequestFactory, StateFactory,
    DayFactory, DateServiceRequestFactory, DayTypeFactory)
from ....resident.test.factories import (
    ResidentFactory, PropertyFactory, PropertyTypeFactory)


class ServiceRequestTest(APITestCase):

    def setUp(self):
        self.model = ServiceRequestFactory._meta.model
        self.factory = ServiceRequestFactory
        self.base_name = 'servicerequest'
        self.url = reverse('%s-list' % self.base_name)
        self.client.force_authenticate(user=UserFactory.build())

        self._property = PropertyFactory(
            property_type=PropertyTypeFactory.create())
        self.date_service_request = DateServiceRequestFactory()
        self.day_type = DayTypeFactory()
        self.day = DayFactory(day_type=self.day_type)

    def tearDown(self):
        pass

    def get_service_request(self, user, _property, date_service_request):
        service_request = ServiceRequestFactory(
            service=ServiceFactory.create(),
            state=StateFactory.create(),
            user=user, _property=_property,
            date_service_request=date_service_request)
        return service_request

    @tag('integration')
    def test_create_service_request_resident_has_credit(self):
        """ Permision class check for the resident has credit, based
        on the sap_customer, '4259' has credit """
        # Arrange
        user = UserFactory.create()
        ResidentFactory(
            user=user, sap_customer=4259)
        service_request = self.get_service_request(
            user, self._property, self.date_service_request)
        data = model_to_dict(service_request)
        data.pop('user')
        data['_property'] = str(self._property.id)
        data['date_service_request'] = model_to_dict(self.date_service_request)
        data['date_service_request']['day'] = [self.day.id]
        self.client.force_authenticate(user=user)

        # Act
        response = self.client.post(self.url, data, format='json')

        # Assert
        eq_(response.status_code, status.HTTP_201_CREATED)
        service = response.json()
        ok_(service.get('id'))
        eq_(service.get('service'), service_request.service.pk)
        eq_(service.get('note'), service_request.note)
        eq_(service.get('phone'), service_request.phone)
        eq_(service.get('email'), service_request.email)
        eq_(service.get('_property'), str(service_request._property.pk))

    @tag('integration')
    def test_create_service_request_resident_has_not_credit(self):
        """ Permision class check for the resident has credit, based
        on the sap_customer, '4635' has credit """
        # Arrange
        user = UserFactory.create()
        ResidentFactory(
            user=user, sap_customer=4635)
        service_request = self.get_service_request(
            user, self._property, self.date_service_request)
        data = model_to_dict(service_request)
        data.pop('user')
        data['_property'] = str(self._property.id)
        data['date_service_request'] = model_to_dict(self.date_service_request)
        data['date_service_request']['day'] = [self.day.id]
        self.client.force_authenticate(user=user)

        # Act
        response = self.client.post(self.url, data, format='json')

        # Assert
        eq_(response.status_code, status.HTTP_403_FORBIDDEN)
        error = response.json()
        eq_(error.get('detail'),
            'Your credit status do not allow you to '
            'create new service requests.')
