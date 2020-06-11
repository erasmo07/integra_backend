# -*- coding: utf-8 -*-
from rest_framework.test import APITestCase
from integrabackend.users.test.factories import (
    ApplicationFactory, UserFactory, AccessApplicationFactory)
from integrabackend.invitation.enums import (
    StatusInvitationEnums, TypeInvitationEnums)
from integrabackend.invitation.test.factories import (
    StatusInvitationFactory, TypeInvitationFactory, MedioFactory,
    ColorFactory, TransportationFactory
)
from integrabackend.resident.test.factories import (
    PropertyFactory, TypeIdentificationFactory)


class InvitationTestBase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        super(InvitationTestBase, cls).setUpTestData()

        # Invitation status
        cls.pending = StatusInvitationFactory.create(
            name=StatusInvitationEnums.pending)

        # Invitation types
        cls.friends_and_family = TypeInvitationFactory.create(
            name=TypeInvitationEnums.friend_and_family
        )
        cls.supplier = TypeInvitationFactory.create(
            name=TypeInvitationEnums.supplier
        )

        cls.cedula = TypeIdentificationFactory.create()

        # Transportation
        cls.truck = MedioFactory.create(
            name='Truck'
        )

        # Colors
        cls.red = ColorFactory.create(
            name='Red'
        )

        cls.a_transport = TransportationFactory(
            medio=cls.truck,
            color=cls.red,
        )

        cls.gpc_application = ApplicationFactory.create(
            name='Portal GPC', merchant__name='GPC',
            merchant__number='0000', domain='domain front')

        cls.gpc_user = UserFactory.create()

        cls.access = AccessApplicationFactory(user=cls.gpc_user)

        # Po
        cls.a_property = PropertyFactory.create()
        cls.another_property = PropertyFactory.create()

    def get_credentials(self, user, access):
        credentials = {
            'HTTP_AUTHORIZATION': 'Token %s' % (user.auth_token.key),
            'HTTP_APPLICATION': 'Bifrost %s' % (access.application_id),
        }
        return credentials
