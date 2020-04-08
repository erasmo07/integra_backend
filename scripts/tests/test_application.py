from django.conf import settings
from django.test import TestCase, override_settings
from django.core import mail
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework import status

from integrabackend.users.test.factories import (AccessApplicationFactory,
                                                 UserFactory, ApplicationFactory)

from .. import application


class TestCreateFather(TestCase):

    def setUp(self):
        self.application = ApplicationFactory.create(
            name='Portal PCIS',
            merchant__name='PCIS',
            merchant__number='0000',
            domain='domain front')

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_user_does_not_exists(self):
        # GIVEN
        row = {
            'name': 'Prueba', 'sap_customer': '0000',
            'email': 'example@example.com',
        }

        # WHEN
        user = application.create_father(row)

        # THEN
        user.refresh_from_db()

        self.assertTrue(user.accessapplication_set.exists())
        self.assertEqual(user.accessapplication_set.count(), 1)

        assert len(mail.outbox) == 1, "Inbox is not empty"
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL
        assert mail.outbox[0].to == ['example@example.com']

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id)).decode()

        assert token in mail.outbox[0].body 
        assert uid in mail.outbox[0].body
        assert self.application.domain in mail.outbox[0].body 

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_user_exists_in_db(self):
        # GIVEN
        row = {
            'name': 'Prueba', 'sap_customer': '0000',
            'email': 'example@example.com',
        }
        UserFactory.create(
            email=row.get('email'),
            username=row.get('email')
        )

        # WHEN
        user = application.create_father(row)

        # THEN
        user.refresh_from_db()

        self.assertTrue(user.accessapplication_set.exists())

        assert len(mail.outbox) == 1, "Inbox is not empty"
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL
        assert mail.outbox[0].to == ['example@example.com']

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id)).decode()

        assert token in mail.outbox[0].body 
        assert uid in mail.outbox[0].body
        assert self.application.domain in mail.outbox[0].body 
    
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_user_exists_with_application_access(self):
        # GIVEN
        row = {
            'name': 'Prueba', 'sap_customer': '0000',
            'email': 'example@example.com',
        }
        user_factory = UserFactory.create(
            email=row.get('email'),
            username=row.get('email')
        )

        AccessApplicationFactory.create(
            user=user_factory,
            application=self.application,
        )

        # WHEN
        user = application.create_father(row)

        # THEN
        user.refresh_from_db()

        self.assertTrue(user.accessapplication_set.exists())
        self.assertEqual(user.accessapplication_set.count(), 1)
        
        assert len(mail.outbox) == 1, "Inbox is not empty"
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL
        assert mail.outbox[0].to == ['example@example.com']
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id)).decode()

        assert token in mail.outbox[0].body 
        assert uid in mail.outbox[0].body
        assert self.application.domain in mail.outbox[0].body 
    
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_integration(self):
        row = {
            'name': 'Prueba', 'sap_customer': '0000',
            'email': 'example@example.com',
        }

        user = application.create_father(row)
        user.refresh_from_db()
        
        self.assertTrue(user.accessapplication_set.exists())
        self.assertEqual(user.accessapplication_set.count(), 1)

        assert len(mail.outbox) == 1, "Inbox is not empty"
        assert mail.outbox[0].from_email == settings.DEFAULT_FROM_EMAIL
        assert mail.outbox[0].to == ['example@example.com']

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id)).decode()

        assert token in mail.outbox[0].body 
        assert uid in mail.outbox[0].body
        assert self.application.domain in mail.outbox[0].body

        response = self.client.post(
            '/rest-auth/password/reset/confirm/',
            {
                'uid': urlsafe_base64_encode(
                    force_bytes(user.id)
                ).decode(),
                'token': default_token_generator.make_token(user),
                'new_password1': '@1234567',
                'new_password2': '@1234567',
            })
        
        self.assertEqual(response.status_code, 200)

        response_login = self.client.post(
            '/api-token-auth/', {
                'username': user.username,
                'password': '@1234567'
            }
        )

        self.assertEqual(response_login.status_code, 200)
        self.assertIn('token', response_login.json())
