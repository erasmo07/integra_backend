from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_

from ..models import Invitation
from ..serializers import InvitationSerializer
from .factories import InvitationFactory, TypeInvitationFactory
from ...resident.test.factories import (
    ResidentFactory, PersonFactory, TypeIdentificationFactory)
from ...users.test.factories import UserFactory


fake = Faker()


class TestInvitationTestCase(APITestCase):
    """
    Tests /invitation list operations.
    """

    def setUp(self):
        self.base_name = 'invitation'
        self.url = reverse('%s-list' % self.base_name)
        invitation = InvitationFactory.create(
            resident=ResidentFactory(user=UserFactory.create()),
            type_invitation=TypeInvitationFactory.create())
        person = PersonFactory.create(
            create_by=ResidentFactory(user=UserFactory.create()), 
            type_identification=TypeIdentificationFactory.create())
        invitation.invitated.add(person)
        self.data = InvitationSerializer(invitation).data
        self.client.force_authenticate(user=UserFactory.build())

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        invitation = Invitation.objects.get(pk=response.data.get('id'))
        eq_(str(invitation.resident.id), self.data.get('resident'))

    def test_get_request_list_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url)
        for invitation in response.json():
            ok_(invitation.get('id'))
            eq_(invitation.get('resident'), self.data.get('resident'))
            eq_(invitation.get('type_invitation'),
                str(self.data.get('type_invitation')))

    def test_get_request_with_pk_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        kwargs = {'pk': response.json().get('id')}
        url = reverse('%s-detail' % self.base_name, kwargs=kwargs)

        response = self.client.get(url)
        invitation = response.json()
        eq_(invitation.get('id'), kwargs.get('pk'))
        eq_(invitation.get('resident'), self.data.get('resident'))
        eq_(invitation.get('type_invitation'),
            str(self.data.get('type_invitation')))

    def test_put_request_success(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED)

        kwargs = {'pk': response.json().get('id')}
        url = reverse('%s-detail' % self.base_name, kwargs=kwargs)

        user = UserFactory.create()
        resident = ResidentFactory(user=user)
        self.data['resident'] = str(resident.id)
        response = self.client.put(url, self.data)

        eq_(response.status_code, status.HTTP_200_OK)
        eq_(response.json().get('resident'), self.data.get('resident'))
        eq_(response.json().get('type_invitation'),
            str(self.data.get('type_invitation')))

class TestTypeInvitationTestCase(APITestCase):
    """
    Tests /type-invitation list operations.
    """

    def setUp(self):
        self.model = TypeInvitationFactory._meta.model
        self.base_name = 'type-invitation'
        self.url = reverse('%s-list' % self.base_name)
        self.client.force_authenticate(user=UserFactory.build())

    def test_get_request_list_succeeds(self):
        TypeInvitationFactory.create()
        response = self.client.get(self.url)
        for type_invitation in response.json():
            ok_(type_invitation.get('id'))
            ok_(type_invitation.get('name') is not None)

    def test_get_request_with_pk_succeeds(self):
        type_invitation = TypeInvitationFactory.create()
        url = reverse(
            '%s-detail' % self.base_name, kwargs={'pk': type_invitation.id})

        response = self.client.get(url)

        type_invitation = response.json()
        ok_(type_invitation.get('id'))
        ok_(type_invitation.get('name') is not None)
