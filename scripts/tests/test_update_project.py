from django.test import TestCase, override_settings
from django.conf import settings
from django.core import mail, management


class TestCommandWork(TestCase):
    fixtures = [
        ''.join([settings.ROOT_PROJECT, '/fixtures/db_integra.json']
    )]

    def test_can_apply_command_on_production(self):
        # WHEN
        management.call_command("runscript", "update_project")