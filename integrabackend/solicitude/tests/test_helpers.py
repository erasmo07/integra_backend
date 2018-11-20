from mock import patch, MagicMock
from django.core import mail
from django.test import TestCase
from faker import Faker
from nose.tools import eq_, ok_

from .factories import (
    ServiceFactory, ServiceRequestFactory, StateFactory,
    DayFactory, DateServiceRequestFactory, DayTypeFactory)
from ...users.test.factories import UserFactory
from integrabackend.resident.test.factories import PropertyFactory, PropertyTypeFactory
from .. import helpers


faker = Faker()


class TestClientValidQuotation(TestCase):

    def setUp(self):
        property = PropertyFactory(
            property_type=PropertyTypeFactory.create())
        date_service_request = DateServiceRequestFactory()
        day_type = DayTypeFactory()
        day = DayFactory(day_type=day_type)
        date_service_request.day.add(day)
        self.service_request = ServiceRequestFactory(
            service=ServiceFactory.create(),
            state=StateFactory.create(),
            user=UserFactory.create(), 
            property=property,
            date_service_request=date_service_request)
    
    @patch('integrabackend.solicitude.helpers.Status')
    def test_generic_user(self, mock_status):
        # WHEN
        helpers.client_valid_quotation(
            self.service_request,
            ticket_class=MagicMock)

        # THEN
        eq_(len(mail.outbox), 1)
