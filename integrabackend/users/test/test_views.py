from random import randint
from django.contrib.auth.hashers import check_password
from django.forms.models import model_to_dict
from django.test import override_settings
from django.urls import reverse
from nose.tools import eq_, ok_
from rest_framework import status
from rest_framework.test import APITestCase

from ...resident.test.factories import ResidentFactory
from ..enums import GroupsEnums
from ..models import User
from .factories import (AccessApplicationFactory, ApplicationFactory,
                        MerchantFactory, UserFactory)


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

        self.assertIn('last_login', response.json())
        self.assertIn('date_joined', response.json())
        self.assertIn('is_active', response.json())

    def test_get_request_find_user_by_params(self):
        response = self.client.get(f'/api/v1/users/?email={self.user.email}')
        eq_(response.status_code, status.HTTP_200_OK)

        self.assertIn('last_login', response.json()[0])
        self.assertIn('date_joined', response.json()[0])

    def test_put_request_updates_a_user(self):
        payload = {'first_name': 'NAME'}
        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(pk=self.user.id)
        eq_(user.first_name, 'NAME')


class TestUserTokenTestCase(APITestCase):
    """
    Test /api-token-auth
    """

    def setUp(self):
        self.url = reverse('token')

    def test_get_request_return_resident_and_token_without_filter(self):
        # when
        response = self.client.get(self.url)

        # then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_request_return_token(self):
        # given
        user = UserFactory.create()

        # when
        response = self.client.get(self.url, {'username': user.username})

        # then
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('token', response.json())

    def test_get_request_return_resident_and_token(self):
        # given
        user = UserFactory.create()
        ResidentFactory(user=user)

        # when
        response = self.client.get(self.url, {'username': user.username})

        # then
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('token', response.json())
        self.assertIn('resident', response.json())

    @override_settings(VALID_APPLICATION=True)
    def test_post_not_send_header(self):
        user = UserFactory()
        user.set_password('1234567')
        user.save()

        data = dict(username=user.username, password='1234567')
        response = self.client.post(self.url, data)

        eq_(response.status_code, status.HTTP_403_FORBIDDEN)
        eq_({'detail': 'Not send correct headers'}, response.json())

    @override_settings(VALID_APPLICATION=True)
    def test_post_user_with_application_access(self):
        user = UserFactory()
        user.set_password('1234567')
        user.save()

        access = AccessApplicationFactory(user=user)
        self.client.credentials(
            HTTP_APPLICATION=f'Bifrost {access.application.id}')

        data = dict(username=user.username, password='1234567')
        response = self.client.post(self.url, data)

        eq_(response.status_code, status.HTTP_200_OK)
        ok_('token' in response.json())

    @override_settings(VALID_APPLICATION=True)
    def test_post_user_with_wrong_application(self):
        user = UserFactory()
        user.set_password('1234567')
        user.save()

        AccessApplicationFactory(user=user)
        access = AccessApplicationFactory(user=UserFactory.create())

        self.client.credentials(
            HTTP_APPLICATION=f'Bifrost {access.application.id}')

        data = dict(username=user.username, password='1234567')
        response = self.client.post(self.url, data)

        eq_(response.status_code, status.HTTP_403_FORBIDDEN)
        eq_('This user does not have permission for this application',
            response.json().get('detail'))

        eq_(access.application.name,
            response.json().get('application'))

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

    def test_post_request_return_default_client(self):
        # GIVEN
        user = UserFactory()
        user.set_password('1234567')
        user.save()

        access = AccessApplicationFactory.create(user=user)
        access.details.create(sap_customer='prueba', default=True)

        # WHEN
        data = dict(username=user.username, password='1234567')
        response = self.client.post(self.url, data)

        # THEN
        eq_(response.status_code, status.HTTP_200_OK)
        ok_('token' in response.json())
        ok_('sap_customer' in response.json())

    def test_post_request_not_has_default_client(self):
        # GIVEN
        user = UserFactory()
        user.set_password('1234567')
        user.save()

        access = AccessApplicationFactory.create(user=user)
        access.details.create(sap_customer='prueba')

        # WHEN
        data = dict(username=user.username, password='1234567')
        response = self.client.post(self.url, data)

        # THEN
        eq_(response.status_code, status.HTTP_200_OK)
        ok_('token' in response.json())
        ok_('sap_customer' not in response.json())


class TestApplication(APITestCase):

    def setUp(self):
        self.url = '/api/v1/application/'
        ApplicationFactory.create(
            name='Test',
            merchant__name='Test',
            merchant__number='Test'
        )

    def test_normal_user_cant_view(self):
        # WHEN
        user = UserFactory.create()
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {user.auth_token}')

        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, 403)

    def test_backoffice_user_cant_view(self):
        # WHEN
        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.backoffice)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {user.auth_token}')

        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, 403)

    def test_application_user_can_view(self):
        # WHEN
        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.application)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {user.auth_token}')

        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class TestAccessApplication(APITestCase):

    def setUp(self):
        self.url = '/api/v1/access-application/'
        self.key = ['id', 'user', 'application', 'details']
        self.key_type = [('application', list), ('details', list)]

        self.factory = AccessApplicationFactory
        for _ in range(5):
            instance = self.factory.create()

            instance.details.create(
                sap_customer='{}'.format(
                    randint(100000, 999999)))

        user = UserFactory.create()
        user.groups.create(name=GroupsEnums.application)

        self.client.force_login(user=user)

    def test_get_request_success(self):
        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in self.key:
            for element in response.json():
                self.assertIn(key, element)

    def test_get_request_filter_by_user(self):
        # GIVEN
        instance = self.factory.create()

        # WHEN
        response = self.client.get(
            self.url, {'user': instance.user.id})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        self.assertEqual(
            str(instance.user.id),
            response.json()[0].get('user'))

    def test_get_request_filter_by_application(self):
        # GIVEN
        instance = self.factory.create()

        # WHEN
        response = self.client.get(
            self.url, {'application': instance.application.id})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        self.assertEqual(
            str(instance.application.id),
            response.json()[0].get('application').get('id'))

    def validate_not_has_access_to_endpoint(self, group_name):
        # WHEN
        user = UserFactory.create()
        user.groups.create(name=group_name)

        self.client.force_login(user=user)
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_monitoring_center_user_cant_view(self):
        self.validate_not_has_access_to_endpoint(GroupsEnums.monitoring_center)
    
    def test_security_agent_user_cant_view(self):
        self.validate_not_has_access_to_endpoint(GroupsEnums.security_agent)

    def test_backoffice_user_cant_view(self):
        self.validate_not_has_access_to_endpoint(GroupsEnums.backoffice)
    
    def test_post_request_return_method_not_allow(self):
        # GIVEN
        data = model_to_dict(self.factory.create())
    
        # WHEN
        response = self.client.post(self.url, data)
    
        # THEN
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_put_request_return_method_not_allow(self):
        # GIVEN
        instance = self.factory.create()
    
        # WHEN
        url = '/api/v1/access-application/{instance.pk}/'
        new_data = model_to_dict(self.factory.create(), exclude=['id'])
        response = self.client.post(self.url, new_data)
    
        # THEN
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED)


class TestMerchant(APITestCase):

    def setUp(self):
        self.url = '/api/v1/merchant/'
        self.factory = MerchantFactory

    def test_cant_normal_user_list_merchant(self):
        # GIVEN
        user = UserFactory.create()
        self.client.force_login(user=user)

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_create_merchant(self):
        # GIVEN
        user = UserFactory()
        user.groups.create(name=GroupsEnums.backoffice)

        self.client.force_authenticate(user=user)

        # WHEN
        data = model_to_dict(self.factory.create(), exclude=['id'])
        response = self.client.post(self.url, data)

        # THEN
        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_can_backoffice_user_list_merchant(self):
        # GIVEN
        user = UserFactory()
        user.groups.create(name=GroupsEnums.backoffice)

        self.client.force_authenticate(user=user)

        for _ in range(5):
            self.factory.create()

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for merchant in response.json():
            self.assertIn('id', merchant)
            self.assertIn('name', merchant)
            self.assertIn('number', merchant)
