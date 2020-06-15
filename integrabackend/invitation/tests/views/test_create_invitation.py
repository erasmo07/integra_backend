# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from integrabackend.invitation.tests.base import InvitationTestBase
from django.urls import reverse
from integrabackend.invitation.models import Invitation
from datetime import date


class InvitationCreateTest(InvitationTestBase, APITestCase):

    def setUp(self):
        self.url = reverse('invitation-list')

        self.invitation_data = {
            'type_invitation': str(self.friends_and_family.pk),
            'invitated': [
                {
                    'name': 'Julio Voltio',
                    'email': 'jvoltio@nomail.com',
                    'identification': '123-0034569-4',
                    'type_identification': str(self.cedula.id),
                }
            ],
            'total_companions': 2,
            'date_entry': '2010-12-31',
            'date_out': '2010-12-31',
            'property': str(self.a_property.pk),
            'note': 'This is a super note.',
        }

    def test_user_create_an_invitation(self):
        # Arrange
        access = self.gpc_user.accessapplication_set.first()
        credentials = self.get_credentials(self.gpc_user, access)

        # Act
        response = self.client.post(self.url, data=self.invitation_data,
                                    format='json', **credentials)

        # Assert
        self.assertEqual(response.status_code, 201)

        invitation_data = self.invitation_data.copy()
        invitation_data.pop('property')

        invitation = Invitation.objects.first()
        for key in invitation_data.keys():
            current_field = getattr(invitation, key)
            if key == 'type_invitation':
                self.assertEqual(current_field, self.friends_and_family)
                continue
            if key == 'invitated':
                continue
            if key == 'date_entry' or key == 'date_out':
                self.assertEqual(current_field, date(2010, 12, 31))
                continue
            self.assertEqual(current_field, invitation_data[key])

        self.assertEqual(invitation.invitated.count(), 1)
