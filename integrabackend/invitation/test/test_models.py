from django.test import TestCase
from django.contrib.auth.models import Permission

from nose.tools import eq_, ok_

from ...users.test.factories import UserFactory
from .. import models
from . import factories


class TestInvitation(TestCase):

    def setUp(self):
        self.model = models.Invitation
        self.user = UserFactory.create()

    def test_permission_check_in(self):
        # GIVEN
        permission = Permission.objects.get(codename='can_check_in')

        # WHEN
        self.user.user_permissions.add(permission)

        # THEN
        ok_(self.user.has_perm('invitation.can_check_in'))
    
    def test_permission_check_out(self):
        # GIVEN
        permission = Permission.objects.get(codename='can_check_out')

        # WHEN
        self.user.user_permissions.add(permission)

        # THEN
        ok_(self.user.has_perm('invitation.can_check_out'))

    def test_permission_invitation_view_invitation(self):
        # GIVEN
        permission = Permission.objects.get(codename='view_invitation')

        # WHEN
        self.user.user_permissions.add(permission)

        # THEN
        ok_(self.user.has_perm('invitation.view_invitation'))
        eq_(False, self.user.has_perm('invitation.add_invitation'))
        eq_(False, self.user.has_perm('invitation.change_invitation'))
        eq_(False, self.user.has_perm('invitation.delete_invitation'))
