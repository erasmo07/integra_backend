import time
from nose.tools import eq_, ok_

from rest_framework.test import APITestCase
from rest_framework import status

from django.urls import reverse
from django.forms.models import model_to_dict
from django.core import mail
from django.conf import settings

from partenon.helpdesk import HelpDeskTicket
from partenon.ERP import ERPAviso

from .factories import (
    ServiceFactory, ServiceRequestFactory, StateFactory,
    DayFactory, DateServiceRequestFactory, DayTypeFactory,
    QuotationFactory)
from integrabackend.solicitude.enums import Subjects, StateEnums
from ...users.test.factories import UserFactory
from integrabackend.resident.test.factories import PropertyFactory, PropertyTypeFactory


class TestServiceRequestTestCase(APITestCase):
    """
    Test /solicitude-service CRUD
    """

    def setUp(self):
        from django.conf import settings
        settings.CELERY_ALWAYS_EAGER = True

        self.model = ServiceRequestFactory._meta.model 
        self.factory = ServiceRequestFactory
        self.base_name = 'servicerequest'
        self.url = reverse('%s-list' % self.base_name)
        self.url_aviso = reverse('create_aviso-list')
    
    def service_request_data(self):
        property = PropertyFactory(
            property_type=PropertyTypeFactory.create())
        date_service_request = DateServiceRequestFactory()
        day_type = DayTypeFactory()
        day = DayFactory(day_type=day_type)
        date_service_request.day.add(day)
        service_request = ServiceRequestFactory(
            service=ServiceFactory.create(),
            state=StateFactory.create(),
            user=UserFactory.create(), 
            property=property,
            sap_customer=4259,
            date_service_request=date_service_request)
        data = model_to_dict(service_request)
        data.pop('user')
        data['property'] = str(property.id)
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
        ok_(service.get('property'))

        # Create aviso
        response_aviso = self.create_aviso(service.get('id'))
        eq_(response_aviso.status_code, status.HTTP_201_CREATED)

        service_object = self.model.objects.get(pk=service.get('id'))
        ok_(service_object.aviso_id is not None)

        # Validate exists aviso
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_aviso'), StateEnums.aviso.initial_status)

        service_object.aviso_id = 514958 
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
        ok_(service.get('property'))

        # Create aviso
        response_aviso = self.create_aviso(service.get('id')) 
        
        eq_(response_aviso.status_code, status.HTTP_201_CREATED)
        service_object = self.model.objects.get(pk=service.get('id'))
        ok_(service_object.aviso_id is not None)

        # Validate exists aviso
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_aviso'), StateEnums.aviso.initial_status)

        service_object.aviso_id = 514958 
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
        ok_(service.get('property'))

        # Create aviso
        response_aviso = self.create_aviso(service.get('id')) 
        
        eq_(response_aviso.status_code, status.HTTP_201_CREATED)
        service_object = self.model.objects.get(pk=service.get('id'))
        ok_(service_object.aviso_id is not None)

        # Validate exists aviso
        aviso_info = ERPAviso().info(service_object.aviso_id)
        eq_(aviso_info.get('estado_aviso'), StateEnums.aviso.initial_status)

        service_object.aviso_id = 514958 
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

        # Validate ServiceRequest
        eq_(service_object.state.name,
            StateEnums.service_request.reject_work)