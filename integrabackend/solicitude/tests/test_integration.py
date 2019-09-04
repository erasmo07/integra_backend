import time
from nose.tools import eq_, ok_

from django.test import TestCase
from rest_framework.test import APITestCase
from django.test import override_settings
from rest_framework import status

from django.urls import reverse
from django.forms.models import model_to_dict
from django.core import mail
from django.conf import settings
from factory import Sequence

from partenon.helpdesk import HelpDeskTicket, HelpDesk
from partenon.ERP import ERPAviso

from .factories import (
    ServiceFactory, ServiceRequestFactory, StateFactory,
    DayFactory, DateServiceRequestFactory, DayTypeFactory,
    QuotationFactory)
from integrabackend.solicitude.enums import Subjects, StateEnums
from ...users.test.factories import UserFactory
from integrabackend.resident.test.factories import (
    PropertyFactory, PropertyTypeFactory, ResidentFactory, ProjectFactory,
    DepartmentFactory, AreaFactory, OrganizationFactory)
from unittest import skip
from django.test import tag
from mock import patch, MagicMock
from ..permissions import HasCreditPermission


class TestServiceRequestTestCase(APITestCase):
    """
    Test /solicitude-service CRUD
    """

    def setUp(self):
        # from django.conf import settings
        # settings.CELERY_ALWAYS_EAGER = True

        self.model = ServiceRequestFactory._meta.model
        self.factory = ServiceRequestFactory
        self.base_name = 'servicerequest'
        self.url = reverse('%s-list' % self.base_name)
        self.url_aviso = reverse('create_aviso-list')

    def service_request_data(self):
        project = ProjectFactory(
            department=DepartmentFactory(),
            area=AreaFactory(organization=OrganizationFactory()))
        _property = PropertyFactory(
            property_type=PropertyTypeFactory.create(),
            project=project)

        date_service_request = DateServiceRequestFactory()
        day_type = DayTypeFactory()
        day = DayFactory(day_type=day_type)
        date_service_request.day.add(day)
        service_request = ServiceRequestFactory(
            service=ServiceFactory.create(),
            state=StateFactory.create(),
            user=UserFactory.create(),
            _property=_property,
            sap_customer=4259,
            date_service_request=date_service_request)

        data = model_to_dict(service_request)
        data.pop('user')
        data['_property'] = str(_property.id)
        data['date_service_request'] = model_to_dict(date_service_request)
        data['date_service_request']['day'] = [day.id]
        service_request.delete()

        return data

    def create_aviso(self, service_request_id):
        service_object = self.model.objects.get(pk=service_request_id)

        params = {'ticket_id': service_object.ticket_id}
        response = self.client.post(self.url_aviso, params)
        return response

    def approve_quotation(self, service_request_id):
        url_detail = reverse(
            "%s-detail" % self.base_name,
            kwargs=dict(pk=service_request_id))
        url_approve = url_detail + 'approve-quotation/'
        return self.client.post(url_approve, {})

    def modify_aviso_to_race(self, aviso_id):
        state_data = {'state': StateEnums.aviso.requires_acceptance_closing}
        url = reverse('create_aviso-detail', kwargs={'pk': aviso_id})
        return self.client.put(url, state_data)

    def modify_aviso_to_raco(self, aviso_id):
        state_data = {'state': StateEnums.aviso.requires_quote_approval}
        url = reverse('create_aviso-detail', kwargs={'pk': aviso_id})
        return self.client.put(url, state_data)

    def approve_work(self, service_request_id):
        url_detail = reverse(
            "%s-detail" % self.base_name,
            kwargs=dict(pk=service_request_id))
        url_approve = url_detail + 'approve-work/'
        return self.client.post(url_approve, {})

    def reject_quotation(self, service_request_id):
        url_detail = reverse(
            "%s-detail" % self.base_name,
            kwargs=dict(pk=service_request_id))
        url_reject = url_detail + 'reject-quotation/'
        return self.client.post(url_reject, {})

    def reject_work(self, service_request_id):
        url_detail = reverse(
            "%s-detail" % self.base_name,
            kwargs=dict(pk=service_request_id))
        url_approve = url_detail + 'reject-work/'
        return self.client.post(url_approve, {})

    @override_settings(CELERY_ALWAYS_EAGER = True)
    @skip('Avoid rate limit.')
    def test_good_path(self):
        # Create service request
        self.client.force_authenticate(user=UserFactory())
        data = self.service_request_data()
        response = self.client.post(self.url, data, format='json')
        eq_(response.status_code, status.HTTP_201_CREATED)

        # Validate service_request
        service = response.json()
        ok_(service.get('id'))
        ok_(service.get('service'))
        ok_(service.get('note'))
        ok_(service.get('phone'))
        ok_(service.get('email'))
        ok_(service.get('_property'))
        ok_('ticket_number' in service.keys())

        # Create aviso
        response_aviso = self.create_aviso(service.get('id'))
        eq_(response_aviso.status_code, status.HTTP_201_CREATED)

        service_object = self.model.objects.get(pk=service.get('id'))
        ok_(service_object.aviso_id is not None)

        # Validate exists aviso
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_aviso'), StateEnums.aviso.initial_status)

        service_object.aviso_id = 521659
        service_object.save()

        # Modify aviso to RACO
        state_data = {'state': StateEnums.aviso.requires_quote_approval}
        url = reverse(
            'create_aviso-detail',
            kwargs={'pk': service_object.aviso_id})
        response_aviso_to_raco = self.client.put(url, state_data)

        # Validate response for change status
        eq_(response_aviso_to_raco.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate quotation
        ok_(service_object.quotation)
        ok_(service_object.quotation.file.__bool__())
        eq_(service_object.quotation.state.name, StateEnums.quotation.pending)

        # Validate ticket
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.waiting_approval_quotation)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.waith_valid_quotation)

        # Validate Email
        email = mail.outbox[0]
        subject = Subjects.build_subject(
            Subjects.valid_quotation, ticket.ticket_number)
        eq_(email.subject, subject)
        ok_(service_object.user.email in email.to)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.cc)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.reply_to)

        # Aprove quotation
        response_aprove_quotation = self.approve_quotation(service.get('id'))

        # Validate response
        eq_(response_aprove_quotation.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate change ticket state
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.aprove_quotation)

        # Validate change aviso state
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_orden'), StateEnums.aviso.aprove_quotation)

        # Validate Quotation
        eq_(service_object.quotation.state.name, StateEnums.quotation.approved)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.approve_quotation)

        # Modify aviso to RACE
        response_aviso_to_race = self.modify_aviso_to_race(service_object.aviso_id)

        # Validate response for change status
        eq_(response_aviso_to_race.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate change ticket state
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.waiting_validate_work)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.waith_valid_work)

        # Validate Email
        email = mail.outbox[1]
        subject = Subjects.build_subject(
            Subjects.valid_work, ticket.ticket_number)
        eq_(email.subject, subject)
        ok_(service_object.user.email in email.to)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.cc)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.reply_to)

        # Approve work
        response_aprove_quotation = self.approve_work(service_object.pk)

        # Validate response for change status
        eq_(response_aviso_to_race.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.approved)

        # Validate change ticket state
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.closed)

        # Validate change status aviso
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_aviso'), StateEnums.aviso.accepted_work)

    @override_settings(CELERY_ALWAYS_EAGER = True)
    @skip('Avoid rate limit.')
    def test_client_reject_quotation(self):
        data = self.service_request_data()

        # Create service request
        self.client.force_authenticate(user=UserFactory())
        response = self.client.post(self.url, data, format='json')
        eq_(response.status_code, status.HTTP_201_CREATED)

        service = response.json()

        ok_(service.get('id'))
        ok_(service.get('service'))
        ok_(service.get('note'))
        ok_(service.get('phone'))
        ok_(service.get('email'))
        ok_(service.get('_property'))

        # Create aviso
        response_aviso = self.create_aviso(service.get('id'))

        eq_(response_aviso.status_code, status.HTTP_201_CREATED)
        service_object = self.model.objects.get(pk=service.get('id'))
        ok_(service_object.aviso_id is not None)

        # Validate exists aviso
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_aviso'), StateEnums.aviso.initial_status)

        service_object.aviso_id = 521659
        service_object.save()

        # Modify aviso to RACO
        response_aviso_to_raco = self.modify_aviso_to_raco(service_object.aviso_id)

        # Validate response for change status
        eq_(response_aviso_to_raco.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate quotation
        ok_(service_object.quotation)
        ok_(service_object.quotation.file.__bool__())
        eq_(service_object.quotation.state.name, StateEnums.quotation.pending)

        # Validate ticket
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.waiting_approval_quotation)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.waith_valid_quotation)

        # Validate Email
        email = mail.outbox[0]
        subject = Subjects.build_subject(
            Subjects.valid_quotation, ticket.ticket_number)
        eq_(email.subject, subject)
        ok_(service_object.user.email in email.to)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.cc)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.reply_to)


        # Reject quotation
        response_reject_quotation = self.reject_quotation(service_object.pk)

        # Validate response
        eq_(response_reject_quotation.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate change ticket state
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.reject_quotation)

        # Validate change aviso state
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_orden'), StateEnums.aviso.reject_quotation)

        # Validate Quotation
        eq_(service_object.quotation.state.name, StateEnums.quotation.reject)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.reject_quotation)

    @override_settings(CELERY_ALWAYS_EAGER = True)
    @skip('Avoid rate limit.')
    def test_client_reject_work(self):
        data = self.service_request_data()

        # Create service request
        self.client.force_authenticate(user=UserFactory())
        response = self.client.post(self.url, data, format='json')
        eq_(response.status_code, status.HTTP_201_CREATED)

        service = response.json()

        ok_(service.get('id'))
        ok_(service.get('service'))
        ok_(service.get('note'))
        ok_(service.get('phone'))
        ok_(service.get('email'))
        ok_(service.get('_property'))

        # Create aviso
        response_aviso = self.create_aviso(service.get('id'))

        eq_(response_aviso.status_code, status.HTTP_201_CREATED)
        service_object = self.model.objects.get(pk=service.get('id'))
        ok_(service_object.aviso_id is not None)

        # Validate exists aviso
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_aviso'), StateEnums.aviso.initial_status)

        service_object.aviso_id = 521659
        service_object.save()

        # Modify aviso to RACO
        response_aviso_to_raco = self.modify_aviso_to_raco(service_object.aviso_id)

        # Validate response for change status
        eq_(response_aviso_to_raco.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate quotation
        ok_(service_object.quotation)
        ok_(service_object.quotation.file.__bool__())
        eq_(service_object.quotation.state.name, StateEnums.quotation.pending)

        # Validate ticket
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.waiting_approval_quotation)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.waith_valid_quotation)

        # Validate Email
        email = mail.outbox[0]
        subject = Subjects.build_subject(
            Subjects.valid_quotation, ticket.ticket_number)
        eq_(email.subject, subject)
        ok_(service_object.user.email in email.to)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.cc)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.reply_to)

        # Aprove quotation
        response_aprove_quotation = self.approve_quotation(service_object.pk)

        # Validate response
        eq_(response_aprove_quotation.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate change ticket state
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.aprove_quotation)

        # Validate change aviso state
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_orden'), StateEnums.aviso.aprove_quotation)

        # Validate Quotation
        eq_(service_object.quotation.state.name, StateEnums.quotation.approved)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.approve_quotation)

        # Modify aviso to RACE
        response_aviso_to_race = self.modify_aviso_to_race(service_object.aviso_id)

        # Validate response for change status
        eq_(response_aviso_to_race.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate change ticket state
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.waiting_validate_work)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.waith_valid_work)

        # Validate Email
        email = mail.outbox[1]
        subject = Subjects.build_subject(
            Subjects.valid_work, ticket.ticket_number)
        eq_(email.subject, subject)
        ok_(service_object.user.email in email.to)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.cc)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.reply_to)

        # Reject work
        response_aprove_quotation = self.reject_work(service_object.pk)

        # Validate response for change status
        eq_(response_aviso_to_race.status_code, status.HTTP_200_OK)
        service_object = self.model.objects.get(pk=service.get('id'))

        # Validate change ticket state
        ticket = HelpDeskTicket.get_specific_ticket(service_object.ticket_id)
        eq_(ticket.state.name, StateEnums.ticket.reject_work)

        # Validate change status aviso
        # aviso_info = ERPAviso().info(service_object.aviso_id)
        # eq_(aviso_info.get('estado_aviso'), StateEnums.aviso.reject_work)

        # Validate send email
        email = mail.outbox[2]
        subject = Subjects.build_subject(
            Subjects.reject_work, ticket.ticket_number)
        aviso = ERPAviso(aviso=service_object.aviso_id)
        eq_(email.subject, subject)
        ok_(aviso.responsable.correo in email.to)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.cc)
        ok_(settings.DEFAULT_SOPORT_EMAIL in email.reply_to)

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.reject_work)

    @override_settings(CELERY_ALWAYS_EAGER = True)
    @skip('Avoid rate limit.')
    def test_create_service_request_for_faveo(self):
        # Login
        self.client.force_authenticate(user=UserFactory())

        # Create user
        user = UserFactory()
        resident = ResidentFactory(user=user, sap_customer=4259)
        property_ = PropertyFactory(property_type=PropertyTypeFactory())
        resident.properties.add(property_)

        # Create user on Faveo
        helpdesk_user = HelpDesk.user.create_user(
            user.email, user.first_name, user.last_name)

        # Create mutiple services
        for i in range(10):
            ServiceFactory(name=f'TEST {i}')
        else:
            last_service = ServiceFactory()

        # Search service by name
        service_url = reverse(
            'service-detail', kwargs={'pk': last_service.id})
        service_response = self.client.get(service_url)
        eq_(service_response.status_code, status.HTTP_200_OK)
        ok_('id' in service_response.json().keys())
        ok_('name' in service_response.json().keys())
        eq_(service_response.json().get('name'), last_service.name)

        # Create ticket on Faveo
        priority = HelpDesk.prioritys.objects.get_by_name('Normal')
        topic = HelpDesk.topics.objects.get_by_name(
            service_response.json().get('name'))
        department = HelpDesk.departments.objects.get_by_name('Informatica y Comunicaciones')
        ticket = helpdesk_user.ticket.create(
        "Solicitud: Test de integracion", 'Prueba de Faveo a Integra',
        priority, topic, department)
        ok_(hasattr(ticket, 'ticket_id'))

        # Search User by email
        user_url = reverse('user-list')
        user_response = self.client.get(user_url, data={"email": user.email})
        eq_(user_response.status_code, status.HTTP_200_OK)
        eq_(len(user_response.json()), 1)
        eq_(user_response.json()[0].get('email'), user.email)
        eq_(user_response.json()[0].get('resident'), user.resident.id)

        # Search Resident by ID
        resident_pk = user_response.json()[0].get('resident')
        url_resident = reverse(
            'resident-detail', kwargs={'pk': resident_pk})
        response_resident = self.client.get(url_resident)
        eq_(response_resident.status_code, status.HTTP_200_OK)
        ok_('properties' in response_resident.json().keys())
        for property_ in response_resident.json().get('properties'):
            ok_('id' in property_.keys())
            ok_('direction' in property_.keys())

        # Search client info
        client_info_url = reverse("client_info-list")
        client_info_sap_customer = response_resident.json().get('sap_customer')
        client_info_response = self.client.get(
            client_info_url, data={'client': client_info_sap_customer})
        eq_(client_info_response.status_code, status.HTTP_200_OK)
        ok_('telefono' in client_info_response.json().keys())
        ok_('e_mail' in client_info_response.json().keys())

        # Search Day service
        day_type = DayTypeFactory()
        day = DayFactory(day_type=day_type)
        day_url = reverse('day-detail', kwargs={'pk': day.id})
        day_response = self.client.get(day_url)
        eq_(day_response.status_code, status.HTTP_200_OK)
        ok_('id' in day_response.json().keys())

        # Build data for create Service Request
        day = list()
        day.append(day_response.json().get('id'))
        data = dict(
            user=user_response.json()[0].get('id'),
            service=service_response.json().get('id'),
            note='Prueba de Faveo a Integra',
            phone=client_info_response.json().get('telefono'),
            email=client_info_response.json().get('e_mail'),
            _property=response_resident.json().get('properties')[0].get('id'),
            date_service_request=dict(
                day=day,
                checking='12:00:00', checkout='12:00:00',
            ),
            sap_customer=response_resident.json().get('sap_customer'),
            require_quotation=False,
            ticket_id=ticket.ticket_id
        )


        # Create service request
        url_faveo = reverse("%s-list" % self.base_name) + 'faveo/'
        self.client.force_authenticate(user=UserFactory())
        response = self.client.post(url_faveo, data, format='json')
        eq_(response.status_code, status.HTTP_201_CREATED)
        service = response.json()

        # Validation
        ok_(service.get('id'))
        eq_(service.get('note'), data.get('note'))
        eq_(service.get('phone'), data.get('phone'))
        eq_(service.get('email'), data.get('email'))
        eq_(service.get('_property'), data.get('_property'))
        eq_(service.get('ticket_id'), ticket.ticket_id)
        eq_(service.get('service'), data.get('service'))
        eq_(service.get('user'), str(user.id))


class ServiceRequestTest(APITestCase):

    def setUp(self):
        self.model = ServiceRequestFactory._meta.model
        self.factory = ServiceRequestFactory
        self.base_name = 'servicerequest'
        self.url = reverse('%s-list' % self.base_name)
        self.client.force_authenticate(user=UserFactory.build())

        self._property = PropertyFactory(
            property_type=PropertyTypeFactory.create())
        self.date_service_request = DateServiceRequestFactory()
        self.day_type = DayTypeFactory()
        self.day = DayFactory(day_type=self.day_type)

    def tearDown(self):
        pass

    def get_service_request(self, user, _property, date_service_request):
        service_request = ServiceRequestFactory(
            service=ServiceFactory.create(),
            state=StateFactory.create(),
            user=user, _property=_property,
            date_service_request=date_service_request)
        return service_request

    @tag('integration')
    def test_create_service_request_resident_has_credit(self):
        """ Permision class check for the resident has credit, based
        on the sap_customer, '4259' has credit """
        # Arrange
        user = UserFactory.create()
        ResidentFactory(
            user=user, sap_customer=4259)
        service_request = self.get_service_request(
            user, self._property, self.date_service_request)
        data = model_to_dict(service_request)
        data.pop('user')
        data['_property'] = str(self._property.id)
        data['date_service_request'] = model_to_dict(self.date_service_request)
        data['date_service_request']['day'] = [self.day.id]
        self.client.force_authenticate(user=user)

        # Act
        response = self.client.post(self.url, data, format='json')

        # Assert
        eq_(response.status_code, status.HTTP_201_CREATED)
        service = response.json()
        ok_(service.get('id'))
        eq_(service.get('service'), service_request.service.pk)
        eq_(service.get('note'), service_request.note)
        eq_(service.get('phone'), service_request.phone)
        eq_(service.get('email'), service_request.email)
        eq_(service.get('_property'), str(service_request._property.pk))

    @tag('integration')
    def test_create_service_request_resident_has_not_credit(self):
        """ Permision class check for the resident has credit, based
        on the sap_customer, '4635' has credit """
        # Arrange
        user = UserFactory.create()
        ResidentFactory(
            user=user, sap_customer=4635)
        service_request = self.get_service_request(
            user, self._property, self.date_service_request)
        data = model_to_dict(service_request)
        data.pop('user')
        data['_property'] = str(self._property.id)
        data['date_service_request'] = model_to_dict(self.date_service_request)
        data['date_service_request']['day'] = [self.day.id]
        self.client.force_authenticate(user=user)

        # Act
        response = self.client.post(self.url, data, format='json')

        # Assert
        eq_(response.status_code, status.HTTP_403_FORBIDDEN)
        error = response.json()
        eq_(error.get('detail'),
            'Your credit status do not allow you to '
            'create new service requests.')


class ResidentHasCreditTest(APITestCase):

    def setUp(self):
        self.base_name = 'client_has_credit'
        self.url = reverse('%s-list' % self.base_name)

        self.client.force_authenticate(user=UserFactory.build())

    def tearDown(self):
        pass

    @tag('integration')
    def test_check_a_resident_has_credit(self):
        # Arrange
        url = self.url + '?code=4259'
        expected = {
            "puede_consumir": True
        }

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)

    @tag('integration')
    def test_check_a_resident_has_not_credit(self):
        # Arrange
        url = self.url + '?code=4635'
        expected = {
            "puede_consumir": False
        }

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected)


class HasCreditPermissionTest(TestCase):

    def setUp(self):
        self.permission = HasCreditPermission()
        self.view = MagicMock()

    def get_request(self, sap_customer):
        user = UserFactory.create()
        ResidentFactory(
            user=user, sap_customer=sap_customer)
        request = MagicMock(user=user)
        return request

    @tag('integration')
    def test_permission_class_returns_true_if_resident_has_credit(self):
        # Arrange
        request = self.get_request(4259)

        # Act and Assert
        self.assertTrue(self.permission.has_permission(request, self.view))

    @tag('integration')
    def test_permission_class_returns_false_if_resident_has_not_credit(self):
        # Arrange
        request = self.get_request(4635)

        # Act and Assert
        self.assertFalse(self.permission.has_permission(request, self.view))
