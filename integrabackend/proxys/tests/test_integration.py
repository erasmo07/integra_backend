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


class TestERPClientViewSet(APITestCase):

    def setUp(self):
        self.url = '/api/v1/sap/client/4259/advance-payment/'
        
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    def test_advance_payment_get_request_success(self):
        # WHEN
        response = self.client.get(self.url, {'merchant': "349052692"})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for advance in response.json():
            self.assertIn('bukrs', advance)
            self.assertIn('concept_id', advance)
            self.assertIn('description', advance)
            self.assertIn('id', advance)
            self.assertIn('spras', advance)
            self.assertIn('status', advance)
    
    def test_society_get_request_success(self):
        # WHEN
        url = '/api/v1/sap/client/4259/society/'
        response = self.client.get(url, {'merchant': "349052692"})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for advance in response.json():
            self.assertIn('company', advance)
            self.assertIn('company_name', advance)

    def test_account_status_get_request_success(self):
        # WHEN
        response = self.client.get(
            '/api/v1/sap/client/4259/account-status-pdf/',
            {
                "lang": "E",
                "merchant": "350000551",
                "date": "20200115"
            })

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.json())
        self.assertIn('success', response.json())
