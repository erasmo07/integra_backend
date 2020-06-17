import datetime
import json
import uuid

from django.conf import settings
from django.core import mail
from django.forms.models import model_to_dict
from django.test import override_settings
from django.urls import reverse
from nose.tools import eq_, ok_
from rest_framework import status
from rest_framework.test import APITestCase

from integrabackend.resident.models import Person

from ...resident.test.factories import (AreaFactory, PersonFactory,
                                        ResidentFactory,
                                        TypeIdentificationFactory)
from ...users.enums import GroupsEnums
from ...users.test.factories import UserFactory
from ..enums import StatusInvitationEnums, TypeInvitationEnums
from ..models import Invitation, Transportation
from ..serializers import InvitationSerializer
from .factories import (CheckInFactory, InvitationFactory,
                        StatusInvitationFactory, TypeInvitationFactory)


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
        self.user = UserFactory.create()
        self.person = PersonFactory.create()
        self.invitation = InvitationFactory.create(
            create_by=self.user,
            invitated=self.person)
        
        self.url = reverse('%s-list' % self.base_name)
        self.url_check_in = f'{self.url}{self.invitation.pk}/check-in/'

        self.factory = InvitationFactory
        self.factory_check_in = CheckInFactory
        self.factory_area = AreaFactory

        self.data = model_to_dict(
            self.invitation, exclude=['id', 'barcode', 'supplier'])
        self.data['property'] = self.data.pop('ownership')
        self.data['invitated'] = model_to_dict(self.person, exclude=['id'])
        self.client.force_authenticate(user=self.user)

        self.data_json = json.loads(json.dumps(self.data, default=default))
    
    def validation_for_success_checkin(self, check_in):
        self.assertEqual(Transportation.objects.count(), 1)

        self.invitation.refresh_from_db()

        self.assertEqual(
            self.invitation.status.name,
            StatusInvitationEnums.check_in)
        
        self.assertIsNotNone(self.invitation.checkin)

        self.assertEqual(self.invitation.invitated, self.invitation.checkin.guest)
        self.assertEqual(check_in.guest.name, self.invitation.invitated.name)
        self.assertEqual(
            check_in.guest.type_identification,
            self.invitation.invitated.type_identification)
        self.assertEqual(
            check_in.guest.identification,
            self.invitation.invitated.identification)

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
            create_by=self.user, invitated=self.person)

        data = model_to_dict(
            self.factory.create(),
            exclude=['id', 'barcode', 'supplier'])
        data['invitated'] = model_to_dict(self.person, exclude=['id'])
        data['property'] = data.pop('ownership')
        data_json = json.loads(json.dumps(data, default=default))

        # WHEN
        url = f'{self.url}{invitation.pk}/'
        response = self.client.put(url, data=data_json, format='json')

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
        response = self.client.post(
            self.url, data=self.data_json, format='json')
        eq_(response.status_code, status.HTTP_201_CREATED)

        invitation = Invitation.objects.get(pk=response.data.get('id'))
        eq_(str(invitation.create_by.id), self.data.get('create_by'))

    def test_get_request_list_succeeds(self):
        response = self.client.post(self.url, self.data_json, format='json')
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
        response = self.client.post(self.url, self.data_json, format='json')

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
        response = self.client.post(self.url, self.data_json, format='json')

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
            type_invitation__name=TypeInvitationEnums.friend_and_family,
            invitated=PersonFactory.create())

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
            status__name=StatusInvitationEnums.pending,
            invitated=PersonFactory.create())

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

        person = PersonFactory.create(
            create_by=self.user,
            type_identification=TypeIdentificationFactory.create())

        invitation = self.factory.create(
            ownership__project__area=area, invitated=person)

        # WHEN
        response = self.client.get(
            self.url, {'invitated__name': person.name})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        eq_(len(response.json()), 1)
        self.assertEqual(
            person.name, 
            response.json()[0].get('invitated').get('name'))

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
    
    def test_only_security_agent_do_checking(self):
        # WHEN
        response = self.client.post(self.url_check_in, {})
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_only_check_in_agent_areas(self):
        # GIVEN
        self.user.groups.create(name=GroupsEnums.security_agent)

        check_in = self.factory_check_in.create(invitation=self.invitation)
        data = model_to_dict(check_in, exclude=['id', 'invitation'])
    
        # WHEN
        response = self.client.post(self.url_check_in, data)
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_only_check_in_type_invitation_allowed(self):
        # GIVEN
        area = self.factory_area.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        self.invitation.ownership.project.area = area
        self.invitation.ownership.project.save()

        check_in = self.factory_check_in.create(invitation=self.invitation)
        data = model_to_dict(check_in, exclude=['id', 'invitation'])
        data['guest'] = model_to_dict(check_in.guest, exclude=['id'])
        data['transport'] = model_to_dict(check_in.transport, exclude=['id'])
        check_in.delete()
    
        # WHEN
        response = self.client.post(self.url_check_in, data, format='json')
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_invitation_only_can_has_one_checkin(self):
        # GIVEN
        area = self.factory_area.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        self.invitation.ownership.project.area = area
        self.invitation.ownership.project.save()

        check_in = self.factory_check_in.create(invitation=self.invitation)
        data = model_to_dict(check_in, exclude=['id', 'invitation'])
        data['guest'] = model_to_dict(check_in.guest, exclude=['id'])
        data['transport'] = model_to_dict(check_in.transport, exclude=['id'])
    
        # WHEN
        response = self.client.post(self.url_check_in, data, format='json')
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_success_path_only_invitated_to_create_checkin(self):
        # GIVEN
        area = self.factory_area.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        self.invitation.ownership.project.area = area
        self.invitation.ownership.project.save()

        check_in = self.factory_check_in.create(invitation=self.invitation)
        data = model_to_dict(check_in, exclude=['id', 'invitation'])
        data['guest'] = model_to_dict(
            check_in.guest,
            fields=['name', 'type_identification', 'identification'])
        data['transport'] = model_to_dict(check_in.transport, exclude=['id'])
        check_in.terminal.check_point.type_invitation_allowed.add(
            self.invitation.type_invitation)

        check_in.delete()
    
        # WHEN
        response = self.client.post(self.url_check_in, data, format='json')
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.validation_for_success_checkin(check_in)
    
    def test_success_path_with_persons_invitated_to_create_checkin(self):
        # GIVEN
        area = self.factory_area.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        self.invitation.ownership.project.area = area
        self.invitation.ownership.project.save()

        check_in = self.factory_check_in.create(invitation=self.invitation)
        data = model_to_dict(check_in, exclude=['id', 'invitation'])
        data['transport'] = model_to_dict(check_in.transport, exclude=['id'])
        data['guest'] = model_to_dict(
            check_in.guest,
            fields=['name', 'type_identification', 'identification'])
        data['persons'] = [
            model_to_dict(
                PersonFactory.create(), exclude=['id']
            ) for _ in range(5)]

        check_in.terminal.check_point.type_invitation_allowed.add(
            self.invitation.type_invitation)

        check_in.delete()
    
        # WHEN
        response = self.client.post(self.url_check_in, data, format='json')
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.validation_for_success_checkin(check_in)

        self.assertEqual(self.invitation.checkin.persons.count(), 5)

    def test_success_path_with_same_person(self):
            # GIVEN
        area = self.factory_area.create()
        self.user.areapermission_set.create(area=area)
        self.user.groups.create(name=GroupsEnums.security_agent)

        self.invitation.ownership.project.area = area
        self.invitation.ownership.project.save()

        check_in = self.factory_check_in.create(
            invitation=self.invitation)

        data = model_to_dict(check_in, exclude=['id', 'invitation'])
        data['transport'] = model_to_dict(
            check_in.transport, exclude=['id'])

        data['guest'] = model_to_dict(
            check_in.guest,
            fields=['name', 'type_identification', 'identification'])

        data['persons'] = [model_to_dict(
            self.person, exclude=['id', 'create_by'])]

        check_in.terminal.check_point.type_invitation_allowed.add(
            self.invitation.type_invitation)

        check_in.delete()
    
        # WHEN
        response = self.client.post(
            self.url_check_in, data, format='json')
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.validation_for_success_checkin(check_in)

        self.assertEqual(self.invitation.checkin.persons.count(), 1)

        self.assertEqual(
            Person.objects.filter(
                **data.get('persons')[0]
            ).count(), 1)


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
