# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from integrabackend.invitation.tests.base import InvitationTestBase
from django.urls import reverse
from integrabackend.invitation.test.factories import InvitationFactory
from integrabackend.resident.test.factories import PersonFactory
from datetime import date


class UpdateInvitationTest(InvitationTestBase, APITestCase):

    def setUp(self):
        self.person = PersonFactory.create(
            create_by=self.gpc_user,
            type_identification=self.cedula,
        )
        self.invitation = InvitationFactory.create(
            create_by=self.gpc_user,
            status=self.pending,
            type_invitation=self.friends_and_family,
            ownership=self.a_property,
            date_entry='2010-11-08',
            date_out='2010-11-08',
            note='Lets have a good time!',
            invitated=self.person
        )
        
        self.url = reverse('invitation-detail', args=[self.invitation.pk])

        self.invitation_data = {
            'type_invitation': str(self.friends_and_family.pk),
            'invitated':{
                'id': str(self.person.id),
                'name': 'Julio Voltio',
                'email': 'jvoltio@nomail.com',
                'identification': '123-0034569-4',
                'type_identification': str(self.person.type_identification.id),
            },
            'total_companions': 2,
            'date_entry': '2010-12-31',
            'date_out': '2010-12-31',
            'property': str(self.another_property.pk),
            'note': 'This is a super note.',
        }

    def test_update_invitation_friends_and_family(self):
        # Arrange
        access = self.gpc_user.accessapplication_set.first()
        credentials = self.get_credentials(self.gpc_user, access)

        # Act
        response = self.client.put(self.url, data=self.invitation_data,
                                   format='json', **credentials)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.total_companions, 2)
        self.assertEqual(self.invitation.date_entry, date(2010, 12, 31))
        self.assertEqual(self.invitation.date_out, date(2010, 12, 31))
        self.assertEqual(self.invitation.ownership, self.another_property)
        self.assertEqual(self.invitation.note, self.invitation_data.get('note'))

        # Assert updated guest :)
        self.assertIsNotNone(self.invitation.invitated)
        self.assertEqual(self.invitation.invitated.name, 'Julio Voltio')
        self.assertEqual(self.invitation.invitated.email, 'jvoltio@nomail.com')
        self.assertEqual(self.invitation.invitated.identification, '123-0034569-4')

    def test_change_invitation_from_friend_to_supplier(self):
        # Arrange
        access = self.gpc_user.accessapplication_set.first()
        credentials = self.get_credentials(self.gpc_user, access)

        invitation_data = self.invitation_data.copy()
        invitation_data.update({
            'type_invitation': str(self.supplier.pk),
            'supplier': {
                'transportation': {
                    'id': str(self.a_transport.pk),
                    'color': str(self.a_transport.color.pk),
                    'medio': str(self.a_transport.medio.pk),
                    'plate': self.a_transport.plate,
                },
                'name': 'Sh it supply',
            }
        })

        # Act
        response = self.client.put(self.url, data=invitation_data,
                                   format='json', **credentials)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.invitation = self.invitation.__class__.objects.get(
            pk=self.invitation.pk)
        self.assertEqual(self.invitation.type_invitation, self.supplier)
        self.assertIsNotNone(self.invitation.supplier)
        self.assertEqual(self.invitation.supplier.name, 'Sh it supply')
