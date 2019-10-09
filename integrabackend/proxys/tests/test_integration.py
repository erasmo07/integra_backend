from django.test import TestCase
from rest_framework.test import APITestCase
from django.test import override_settings
from rest_framework import status

class TestFaveoTicketDetailTestCase(APITestCase):

    def test_get_request_success(self):
        # WHEN
        url = '/api/v1/ticket/34484'
        response = self.client.get(url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get('success'))

