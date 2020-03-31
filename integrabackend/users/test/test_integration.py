import time
from nose.tools import eq_, ok_

from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.forms.models import model_to_dict

from ...users.test.factories import UserFactory


class TestUserTestCase(APITestCase):

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('user-list')
        self.user_data = model_to_dict(UserFactory.build())
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token}') 
    
    def test_get_requet_with_filter_email(self):
        response_create = self.client.post(self.url, self.user_data)
        eq_(response_create.status_code, status.HTTP_201_CREATED)

        params = {'email': response_create.data.get('email')}

        response_search = self.client.get(self.url, params)
        eq_(response_search.status_code, status.HTTP_200_OK)
        eq_(response_search.json()[0].get('email'), response_create.data.get('email'))
        eq_(response_search.json()[0].get('id'), str(response_create.data.get('id')))
    
    def test_get_request_with_filter_email_and_not_exists(self):
        params = {'email': "test@puntacana.com"}

        response_search = self.client.get(self.url, params)
        eq_(response_search.status_code, status.HTTP_200_OK)
        eq_(response_search.json(), [])
    
    def test_post_request_with_exists_email(self):
        response_first = self.client.post(self.url, self.user_data)
        eq_(response_first.status_code, status.HTTP_201_CREATED)

        self.user_data['username'] = 'not-exists'
        response = self.client.post(self.url, self.user_data)
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)
        ok_(not 'username' in response.json().keys())
        eq_(response.json().get('email'),
            ['user with this email already exists.'])