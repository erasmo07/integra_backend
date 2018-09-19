from django.urls import reverse
from django.forms.models import model_to_dict
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_

from ..models import Resident
from .factories import ResidentFactory
from ...users.test.factories import UserFactory


fake = Faker()


class TestResidentListTestCase(APITestCase):
    """
    Tests /resident list operations.
    """

    def setUp(self):
        self.url = reverse('resident-list')
        self.data = model_to_dict(ResidentFactory.build())
        self.client.force_authenticate(user=UserFactory.build())

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        resident = Resident.objects.get(pk=response.data.get('id'))
        eq_(resident.name, self.data.get('name'))
        eq_(resident.email, self.data.get('email'))
        eq_(resident.telephone, self.data.get('telephone'))
        ok_(resident.is_active)
