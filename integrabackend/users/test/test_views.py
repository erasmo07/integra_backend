from django.urls import reverse
from django.forms.models import model_to_dict
from django.contrib.auth.hashers import check_password
from nose.tools import ok_, eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker
from ..models import User
from .factories import UserFactory
from ...resident.test.factories import ResidentFactory 

fake = Faker()


class TestUserListTestCase(APITestCase):
    """
    Tests /users list operations.
    """

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('user-list')
        self.user_data = model_to_dict(UserFactory.build())
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.user_data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(pk=response.data.get('id'))
        eq_(user.username, self.user_data.get('username'))
        ok_(check_password(self.user_data.get('password'), user.password))
    
    def test_get_requet_with_filter_values(self):
        response = self.client.post(self.url, self.user_data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        params = {
            'username': response.data.get('username'),
            'email': response.data.get('email')
        }
        response = self.client.get(self.url, params)
        eq_(response.status_code, status.HTTP_200_OK)


class TestUserDetailTestCase(APITestCase):
    """
    Tests /users detail operations.
    """

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('user-detail', kwargs={'pk': self.user.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_get_request_returns_a_given_user(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)

    def test_put_request_updates_a_user(self):
        new_first_name = fake.first_name()
        payload = {'first_name': new_first_name}
        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(pk=self.user.id)
        eq_(user.first_name, new_first_name)


class TestUserTokenTestCase(APITestCase):
    """
    Test /api-token-auth
    """

    def setUp(self):
        self.url = reverse('token')

    def test_post_request_not_return_resident(self):
        user = UserFactory()
        user.set_password('1234567')
        user.save()

        data = dict(username=user.username, password='1234567')
        response = self.client.post(self.url, data)
        
        eq_(response.status_code, status.HTTP_200_OK)
        ok_('token' in response.json().keys())
        ok_('resident' not in response.json().keys())

    def test_post_request_not_return_resident(self):
        user = UserFactory()
        user.set_password('1234567')
        user.save()

        data = dict(username=user.username, password='1234567')
        response = self.client.post(self.url, data)
        
        eq_(response.status_code, status.HTTP_200_OK)
        ok_('token' in response.json().keys())
        ok_('resident' not in response.json().keys())

    def test_post_request_return_resident(self):
        user = UserFactory()
        user.set_password('1234567')
        user.save()

        ResidentFactory(user=user)

        data = dict(username=user.username, password='1234567')
        response = self.client.post(self.url, data)
        
        eq_(response.status_code, status.HTTP_200_OK)
        ok_('token' in response.json().keys())
        ok_('resident' in response.json().keys())