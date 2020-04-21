from django.conf import settings
from django.test import TestCase, override_settings
from django.core import mail, management
from django.urls import reverse

from rest_framework import status

from integrabackend.resident.test.factories import ResidentFactory
from integrabackend.users.models import User, AccessApplication

from .. import application


class TestCommandWork(TestCase):
    fixtures = [
        ''.join([settings.ROOT_PROJECT, '/fixtures/db_integra.json']
    )]

    def test_can_apply_command_on_production(self):
        # WHEN
        management.call_command("runscript", "migrate_user")

        # THEN
        users = User.objects.filter(password__isnull=False)
        access = AccessApplication.objects.filter(
            user__password__isnull=False,
            application__name='PORTAL CLIENTES')
        self.assertEqual(access.count(), users.count())