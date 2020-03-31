from mock import patch, MagicMock
from django.core import mail
from django.test import TestCase
from nose.tools import eq_, ok_

from .factories import (
    ServiceFactory, ServiceRequestFactory, StateFactory,
    DayFactory, DateServiceRequestFactory, DayTypeFactory)
from ...users.test.factories import UserFactory
from integrabackend.resident.test.factories import (
    PropertyFactory, PropertyTypeFactory, DepartmentFactory,
    AreaFactory, ProjectFactory, OrganizationFactory)
from .. import helpers


def create_service_request():
    project = ProjectFactory(
        department=DepartmentFactory(),
        area=AreaFactory(organization=OrganizationFactory()))
    _property = PropertyFactory(
        property_type=PropertyTypeFactory.create(),
        project=project)
   
    date_service_request = DateServiceRequestFactory()
    day_type = DayTypeFactory()
    day = DayFactory(day_type=day_type)
    date_service_request.day.add(day)
    return ServiceRequestFactory(
        service=ServiceFactory.create(),
        state=StateFactory.create(),
        user=UserFactory.create(), 
        _property=_property,
        date_service_request=date_service_request)


class TestClientValidQuotation(TestCase):

    def setUp(self):
        self.service_request = create_service_request()
        
    @patch('integrabackend.solicitude.helpers.notify_valid_quotation')
    @patch('integrabackend.solicitude.helpers.make_quotation')
    @patch('integrabackend.solicitude.helpers.Status')
    def test_generic_user(self, mock_status, mock_quotation, mock_notification):
        # WHEN
        helpers.client_valid_quotation(
            self.service_request,
            ticket_class=MagicMock,
            ticket_state=MagicMock())

        # THEN
        mock_quotation.assert_called()

        expect_status = helpers.enums.StateEnums.service_request.waith_valid_quotation
        self.assertEqual(self.service_request.state.name, expect_status)

        mock_notification.assert_called()
    

class TestCreateServiceRequest(TestCase):

    def setUp(self):
        self.service_request = create_service_request()
    
    def test_generic_user(self):
        # GIVEN
        helpdesk_class = MagicMock()
        user = MagicMock()
        ticket = MagicMock()
        ticket.ticket_id = 1
        ticket.ticket_number = 'N1'
        user.ticket.create.return_value = ticket
        user.ticket.get_specific_ticket.return_value = ticket 
        user.create_user.return_value = user
        helpdesk_class.topics.objects.get_by_name.return_value = ''
        helpdesk_class.prioritys.objects.get_by_name.return_value = ''
        helpdesk_class.user = user

        self.service_request.ticket_id = None
        self.service_request.save()

        # WHEN
        instance = helpers.create_service_request(
            self.service_request,
            helpdesk_class=helpdesk_class)
        
        # THEN
        self.assertEqual(instance.ticket_id, 1)

        user.create_user.assert_called()
        user.ticket.create.assert_called()
        helpdesk_class.topics.objects.get_by_name.assert_called()
        helpdesk_class.prioritys.objects.get_by_name.assert_called()
        
