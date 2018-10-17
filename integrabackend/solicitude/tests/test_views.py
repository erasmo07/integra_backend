from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_

from .factories import ServiceFactory
from ...users.test.factories import UserFactory


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
        for item in response.json():
            ok_(item.get('id'))
            ok_(item.get('name') is not None)

    def test_get_request_with_pk_succeeds(self):
        service = self.factory.create()
        url = reverse(
            '%s-detail' % self.base_name,
            kwargs={'pk': service.id})

        response = self.client.get(url)

        service = response.json()
        ok_(service.get('id'))
        ok_(service.get('name') is not None)