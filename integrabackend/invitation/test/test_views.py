from django.urls import reverse
from django.core import mail
from django.forms.models import model_to_dict
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_

from ..models import Invitation
from ..enums import StatusInvitationEnums
from ..serializers import InvitationSerializer
from .factories import InvitationFactory, TypeInvitationFactory
from ...resident.test.factories import (
    ResidentFactory, PersonFactory, TypeIdentificationFactory)
from ...users.test.factories import UserFactory


class TestInvitationTestCase(APITestCase):
    """
    Tests /invitation list operations.
    """

    def setUp(self):
        self.base_name = 'invitation'
        self.url = reverse('%s-list' % self.base_name)
        self.user = UserFactory.create()
        invitation = InvitationFactory.create(create_by=self.user)
        person = PersonFactory.create(
            create_by=self.user,
            type_identification=TypeIdentificationFactory.create())
        invitation.invitated.add(person)

        self.factory = InvitationFactory
        self.data = model_to_dict(invitation, exclude=['id'])
        self.data['property'] = self.data.pop('ownership')
        self.client.force_authenticate(user=self.user)
    
    def test_put_request_cant_update_invitation_checkin(self):
        # GIVEN
        invitation = self.factory.create(
            status__name=StatusInvitationEnums.check_in)

        data = model_to_dict(self.factory.create(), exclude=['id'])
        data['property'] = data.pop('ownership')

        # WHEN
        url = f'{self.url}{invitation.pk}/'
        response = self.client.put(url, data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        invitation.refresh_from_db()
        self.assertNotEqual(invitation.date_entry, data.get('date_entry'))
        self.assertNotEqual(invitation.date_out, data.get('date_out'))
        self.assertNotEqual(invitation.note, data.get('note'))

    def test_put_request_can_update_invitation(self):
        # GIVEN
        invitation = self.factory.create(
            status__name=StatusInvitationEnums.pending)

        data = model_to_dict(self.factory.create(), exclude=['id'])
        data['property'] = data.pop('ownership')

        # WHEN
        url = f'{self.url}{invitation.pk}/'
        response = self.client.put(url, data)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invitation.refresh_from_db()
        self.assertEqual(invitation.date_entry, data.get('date_entry'))
        self.assertEqual(invitation.date_out, data.get('date_out'))
        self.assertEqual(invitation.note, str(data.get('note')))

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        invitation = Invitation.objects.get(pk=response.data.get('id'))
        eq_(str(invitation.create_by.id), self.data.get('create_by'))

    def test_get_request_list_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url)
        for invitation in response.json():
            ok_(invitation.get('id'))
            eq_(invitation.get('resident'), self.data.get('resident'))
            eq_(invitation.get('type_invitation'), 'Pending')
            self.assertIn('property', invitation)

    def test_get_request_with_pk_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        kwargs = {'pk': response.json().get('id')}
        url = reverse('%s-detail' % self.base_name, kwargs=kwargs)

        response = self.client.get(url)
        invitation = response.json()
        eq_(invitation.get('id'), kwargs.get('pk'))
        eq_(invitation.get('resident'), self.data.get('resident'))
        eq_(invitation.get('type_invitation'), 'Pending')
        self.assertIn('property', invitation)


class TestTypeInvitationTestCase(APITestCase):
    """
    Tests /type-invitation list operations.
    """

    def setUp(self):
        self.model = TypeInvitationFactory._meta.model
        self.url = '/api/v1/type-invitation/'
        self.client.force_authenticate(user=UserFactory.build())

    def test_get_request_list_succeeds(self):
        TypeInvitationFactory.create()
        response = self.client.get(self.url)
        for type_invitation in response.json():
            ok_(type_invitation.get('id'))
            ok_(type_invitation.get('name') is not None)

    def test_get_request_with_pk_succeeds(self):
        type_invitation = TypeInvitationFactory.create()
        url = '/api/v1/type-invitation/%s/' % str(type_invitation.id)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        type_invitation = response.json()
        ok_(type_invitation.get('id'))
        ok_(type_invitation.get('name') is not None)
