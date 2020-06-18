# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from integrabackend.invitation.tests.base import InvitationTestBase
from django.core import mail
from django.urls import reverse
from integrabackend.invitation.test.factories import (
    InvitationFactory, SupplierFactory)
from integrabackend.resident.test.factories import PersonFactory


class UpdateInvitationTest(InvitationTestBase, APITestCase):

    def setUp(self):
        self.a_supplier = SupplierFactory.create(
            name='Accareos calamardo.',
            transportation=self.a_transport,
        )
        self.person = PersonFactory.create(
            create_by=self.gpc_user,
            type_identification=self.cedula,
        )
        self.invitation = InvitationFactory.create(
            create_by=self.gpc_user,
            status=self.pending,
            type_invitation=self.supplier,
            ownership=self.a_property,
            supplier=self.a_supplier,
            date_entry='2010-11-08',
            date_out='2010-11-08',
            note='Lets have a good time!',
            invitated=self.person
        )
        self.url = reverse('invitation-detail', args=[self.invitation.pk])

        self.expected_json = {
            'type_invitation': str(self.supplier.pk),
            'invitated': {
                'id': str(self.person.id),
                'name': self.person.name,
                'email': self.person.email,
                'identification': self.person.identification,
                'type_identification': str(self.person.type_identification.id),
            },
            'total_companions': 0,
            'property': str(self.a_property.pk),
            'date_entry': '2010-11-08',
            'date_out': '2010-11-08',
            'note': self.invitation.note,
            'supplier': {
                'id': str(self.a_supplier.pk),
                'transportation': {
                    'id': str(self.a_transport.pk),
                    'color': str(self.a_transport.color.pk),
                    'medio': str(self.a_transport.medio.pk),
                    'plate': self.a_transport.plate,
                },
                'name': self.a_supplier.name,
            }
        }

    def test_retrieve_invitation_supplier(self):
        # Arrange
        access = self.gpc_user.accessapplication_set.first()
        credentials = self.get_credentials(self.gpc_user, access)

        # Act
        response = self.client.get(self.url, **credentials)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.expected_json)
        self.assertEqual(len(mail.outbox), 0)
