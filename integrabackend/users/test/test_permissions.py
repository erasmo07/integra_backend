from django.urls import reverse
from rest_framework import status

from django.test import TestCase, override_settings


from . import factories


class TestApplicationAuthorize(TestCase):

    def setUp(self):
        self.user = factories.UserFactory.create()
        self.client.force_login(self.user)

        self.url = '/api/v1/'

    @override_settings(VALID_APPLICATION=True)
    def test_user_can_not_request_application(self):
        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(VALID_APPLICATION=True)
    def test_user_can_request_application(self):
        # GIVEN
        access = factories.AccessApplicationFactory(user=self.user)

        # WHEN
        header = {'HTTP_APPLICATION' :'Bifrost %s' % str(access.application_id)}
        response = self.client.get(self.url, **header)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @override_settings(VALID_APPLICATION=True)
    def test_not_send_valid_keyword(self):
        # GIVEN
        access = factories.AccessApplicationFactory(user=self.user)

        # WHEN
        header = {'HTTP_APPLICATION' :'Key %s' % str(access.application_id)}
        response = self.client.get(self.url, **header)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)