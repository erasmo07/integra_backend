from django.urls import reverse
from django.core import mail
from django.forms.models import model_to_dict
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from nose.tools import eq_, ok_

from ..models import Invitation
from ..enums import StatusInvitationEnums, TypeInvitationEnums
from ..serializers import InvitationSerializer
from .factories import InvitationFactory, TypeInvitationFactory, StatusInvitationFactory
from ...resident.test.factories import (
    ResidentFactory, PersonFactory, TypeIdentificationFactory,
    AreaFactory)
from ...users.test.factories import UserFactory
from ...users.enums import GroupsEnums
import json
import datetime
from django.conf import settings
import uuid
from integrabackend.resident.models import Person


def default(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.strftime(settings.DATE_FORMAT)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Person):
        return model_to_dict(obj)
    raise TypeError("Type %s not serializable" % type(obj))


def unit_disabled(func):
    def wrapper(func):
        func.__test__ = False
        return func

    return wrapper


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
        self.data = model_to_dict(
            invitation, exclude=['id', 'barcode', 'supplier'])
        self.data['property'] = self.data.pop('ownership')
        self.client.force_authenticate(user=self.user)

        self.data_json = json.loads(json.dumps(self.data, default=default))

    def test_put_request_cant_update_invitation_checkin(self):
        # GIVEN
        invitation = self.factory.create(
            status__name=StatusInvitationEnums.check_in,
            create_by=self.user)

        data = model_to_dict(self.factory.create(), exclude=['id', 'barcode'])
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
            status__name=StatusInvitationEnums.pending,
            create_by=self.user)

        data = model_to_dict(
            self.factory.create(),
            exclude=['id', 'barcode', 'supplier'])
        data['property'] = data.pop('ownership')
        data_json = json.loads(json.dumps(data, default=default))

        # WHEN
        url = f'{self.url}{invitation.pk}/'
        response = self.client.put(url, data=data_json, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invitation.refresh_from_db()
        self.assertEqual(invitation.date_entry, data.get('date_entry').date())
        self.assertEqual(invitation.date_out, data.get('date_out').date())
        self.assertEqual(invitation.note, str(data.get('note')))

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, data=self.data_json)
        eq_(response.status_code, status.HTTP_201_CREATED)

        invitation = Invitation.objects.get(pk=response.data.get('id'))
        eq_(str(invitation.create_by.id), self.data.get('create_by'))

    def test_get_request_list_succeeds(self):
        response = self.client.post(self.url, self.data_json)
        eq_(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url)
        for invitation in response.json():
            ok_(invitation.get('id'))
            eq_(invitation.get('resident'), self.data.get('resident'))
            eq_(invitation.get('type_invitation'), 'Pending')
            self.assertIn('property', invitation)

    @unit_disabled
    def skip_test_get_request_with_pk_succeeds(self):
        '''skipped due to another test, check we get specific fields
        in detail APP-258'''
        response = self.client.post(self.url, self.data_json)
        eq_(response.status_code, status.HTTP_201_CREATED)

        kwargs = {'pk': response.json().get('id')}
        url = reverse('%s-detail' % self.base_name, kwargs=kwargs)

        response = self.client.get(url)
        invitation = response.json()
        eq_(invitation.get('id'), kwargs.get('pk'))
        eq_(invitation.get('resident'), self.data.get('resident'))
        eq_(invitation.get('type_invitation'), 'Pending')
        self.assertIn('property', invitation)

    def test_cant_backoffice_resend_invitation(self):
        # GIVEN
        response = self.client.post(self.url, self.data_json)

        # WHEN
        user = UserFactory()
        user.groups.create(name=GroupsEnums.backoffice)
        self.client.force_authenticate(user=user)

        pk = response.json().get('id')
        url = f'/api/v1/invitation/{pk}/resend-notification/'
        response = self.client.post(url, {})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cant_application_resend_invitation(self):
        # GIVEN
        response = self.client.post(self.url, self.data_json)

        # WHEN
        user = UserFactory()
        user.groups.create(name=GroupsEnums.application)
        self.client.force_authenticate(user=user)

        pk = response.json().get('id')
        url = f'/api/v1/invitation/{pk}/resend-notification/'
        response = self.client.post(url, {})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invitation_not_pending_cant_resend_invitation(self):
        # GIVEN
        invitation = InvitationFactory.create(
            create_by=self.user,
            status__name=StatusInvitationEnums.check_in)

        # WHEN
        url = f'/api/v1/invitation/{invitation.pk}/resend-notification/'
        response = self.client.post(url, {})

        # THEN
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_owner_invitation_resend_invitation(self):
        # GIVEN
        invitation = InvitationFactory.create(
            create_by=self.user,
            status__name=StatusInvitationEnums.pending,
            type_invitation__name=TypeInvitationEnums.friend_and_family)
        invitation.invitated.add(PersonFactory.create())

        # WHEN
        url = f'/api/v1/invitation/{invitation.pk}/resend-notification/'
        response = self.client.post(url, {})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 1)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status.name, StatusInvitationEnums.pending)

    def test_cant_cancel_invitation_not_pending(self):
        # GIVEN
        invitation = InvitationFactory.create(
            create_by=self.user,
            status__name=StatusInvitationEnums.check_in)

        # WHEN
        url = f'/api/v1/invitation/{invitation.pk}/cancel/'
        response = self.client.post(url, {})

        # THEN
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_owner_want_cancel_invitaton_pending(self):
        # GIVEN
        invitation = InvitationFactory.create(
            create_by=self.user,
            status__name=StatusInvitationEnums.pending)
        invitation.invitated.add(PersonFactory.create())

        # WHEN
        url = f'/api/v1/invitation/{invitation.pk}/cancel/'
        response = self.client.post(url, {})

        # THEN
        invitation.refresh_from_db()
        self.assertEqual(
            invitation.status.name,
            StatusInvitationEnums.cancel)

    def test_cant_see_invitation_from_other_area(self):
        # GIVEN
        area = AreaFactory.create()
        self.user.areapermission_set.create(area=area)

        invitation = self.factory.create()

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.json():
            self.assertNotEqual(item.get('id'), str(invitation.id))

    def test_can_see_invitation_for_area(self):
        # GIVEN
        area = AreaFactory.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        invitation = self.factory.create(ownership__project__area=area)

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.json():
            self.assertEqual(item.get('id'), str(invitation.id))

    def test_serializer_return_expects_keys(self):
        # GIVEN
        area = AreaFactory.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        invitation = self.factory.create(ownership__project__area=area)

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.json():
            self.assertIn('area', item)
            self.assertIn('property', item)

    def test_can_search_by_invitated_name(self):
        # GIVEN
        area = AreaFactory.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        for _ in range(5):
            self.factory.create(
                ownership__project__area=area)

        invitation = self.factory.create(
            ownership__project__area=area)
        person = PersonFactory.create(
            create_by=self.user,
            type_identification=TypeIdentificationFactory.create())
        invitation.invitated.add(person)

        # WHEN
        response = self.client.get(
            self.url, {'invitated__name': person.name})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        eq_(len(response.json()), 1)
        self.assertEqual(
            person.name, 
            response.json()[0].get('invitated')[0].get('name'))

    def test_can_search_by_property_address(self):
        # GIVEN
        area = AreaFactory.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        for _ in range(5):
            self.factory.create(ownership__project__area=area)

        invitation = self.factory.create(
            ownership__project__area=area,
            ownership__address='Address')

        # WHEN
        response = self.client.get(
            self.url,
            {'ownership__address': invitation.ownership.address})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        eq_(len(response.json()), 1)
        eq_(invitation.ownership.address,
            response.json()[0].get('property'))

    def test_can_filter_by_invitation_number(self):
        # GIVEN
        area = AreaFactory.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        for _ in range(5):
            self.factory.create(ownership__project__area=area)

        invitation = self.factory.create(
            ownership__project__area=area)

        # WHEN
        response = self.client.get(
            self.url, {'number': invitation.number})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        eq_(len(response.json()), 1)
        eq_(str(invitation.number), response.json()[0].get('number'))
    
    def validate_response_filter(self, invitation, filters):
        # WHEN
        self.user.groups.create(name=GroupsEnums.application)
        response = self.client.get(self.url, filters)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        self.assertEqual(
            response.json()[0].get('id'),
            invitation.id)

    def test_can_filter_by_status(self):
        # GIVEN
        for _ in range(5):
            self.factory.create(
                status__name=StatusInvitationEnums.pending)

        invitation = self.factory.create(
            status__name=StatusInvitationEnums.check_in)

        # WHEN
        self.validate_response_filter(
            invitation, {'status': invitation.status.pk})

    def test_can_filter_by_date_in(self):
        # GIVEN
        for _ in range(5):
            self.factory.create()

        invitation = self.factory.create()

        # WHEN
        date_entry = invitation.date_entry.strftime("%Y-%m-%d")
        self.validate_response_filter(invitation, {'date_entry': date_entry})

    def test_can_filter_by_property_address(self):
        # GIVEN
        for _ in range(5):
            self.factory.create()

        invitation = self.factory.create(ownership__address='Dirección')

        self.validate_response_filter(invitation, {'search': invitation.ownership.address})

    def test_can_filter_by_number(self):
            # GIVEN
        for _ in range(5):
            self.factory.create()
        invitation = self.factory.create()

        # WHEN
        self.validate_response_filter(invitation, {'search': invitation.number})


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


class TestStatusInvitation(APITestCase):

    def setUp(self):
        self.url = '/api/v1/status-invitation/'

        self.user = UserFactory.create()
        self.user.groups.create(name=GroupsEnums.application)
        self.client.force_login(user=self.user)

    def test_get_request_success(self):
        # GIVEN
        StatusInvitationFactory.create(name=StatusInvitationEnums.cancel)

        # WHEN
        response = self.client.get(self.url)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
