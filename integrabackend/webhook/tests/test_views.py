import random
from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse_lazy

from partenon.helpdesk import HelpDesk, HelpDeskTicket 
from integrabackend.users.test.factories import UserFactory
from integrabackend.solicitude import enums, helpers
from integrabackend.solicitude.tests import (
    factories as solicitude_factory)


class TestFaveoWebHook(APITestCase):

    def setUp(self):
        self.solicitude = solicitude_factory.ServiceRequestFactory()
        self.url = "/api/v1/faveo-webhook/"
    
    def test_faveo_try_to_close_service_request(self):
        # GIVEN
        data = {
            'event': 'ticket_status_updated',
            'ticket[id]': self.solicitude.ticket_id,
            'ticket[status]': 3
        }
    
        # WHEN
        response = self.client.post(self.url, data, format='json')
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.solicitude.refresh_from_db()
        self.assertEqual(
            self.solicitude.state.name,
            enums.StateEnums.service_request.closed)
    
    def test_faveo_try_to_close_service_request_with_aviso(self):
        # GIVEN
        solicitude = solicitude_factory.ServiceRequestFactory(ticket_id=None)
        helpers.create_service_request(solicitude)

        solicitude.aviso_id = random.randint(1, 20)
        solicitude.save()

        data = {
            'event': 'ticket_status_updated',
            'ticket[id]': solicitude.ticket_id,
            'ticket[status]': 3
        }
    
        # WHEN
        response = self.client.post(self.url, data, format='json')
    
        # THEN
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST)

        solicitude.refresh_from_db()
        self.assertNotEqual(
            solicitude.state.name,
            enums.StateEnums.service_request.closed)
        
        self.assertEqual(
            solicitude.ticket.status_name,
            enums.StateEnums.ticket.open)