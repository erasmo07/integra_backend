from django.test import TestCase
from rest_framework.test import APITestCase
from django.test import override_settings
from rest_framework import status

from integrabackend.users.test.factories import UserFactory
from integrabackend.solicitude.tests.test_helpers import create_service_request
from integrabackend.solicitude import helpers


class TestFaveoTicketDetailTestCase(APITestCase):
    
    def setUp(self):
        self.solicitude = create_service_request()
        helpers.create_service_request(self.solicitude)

        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_get_request_success(self):
        # WHEN
        response = self.client.get(
            '/api/v1/faveo/ticket/%s/' % self.solicitude.ticket_id)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get('success'))

