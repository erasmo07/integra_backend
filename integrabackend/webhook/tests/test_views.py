from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse_lazy

from integrabackend.users.test.factories import UserFactory
from integrabackend.solicitude import enums
from integrabackend.solicitude.tests import (
    factories as solicitude_factory)


class TestFaveoWebHook(APITestCase):

    def setUp(self):
        self.solicitude = solicitude_factory.ServiceRequestFactory()
        self.url = "/api/v1/faveo-webhook/"
        self.client.force_authenticate(user=UserFactory.build())
    
    def test_faveo_try_to_close_service_request(self):
        # GIVEN
        data = {
            'event': 'ticket_status_updated',
            'ticket': {
                'id': self.solicitude.ticket_id,
                'status': 2,
                'statuses': {
                    'name': enums.StateEnums.ticket.closed
                }
            }
        }
    
        # WHEN
        response = self.client.post(self.url, data, format='json')
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.solicitude.refresh_from_db()
        self.assertEqual(
            self.solicitude.state.name,
            enums.StateEnums.service_request.closed)