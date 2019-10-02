from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import render, get_object_or_404
from ..solicitude.models import ServiceRequest, State
from ..solicitude import enums
from integrabackend.solicitude.views import get_value_or_404
from partenon.helpdesk import HelpDesk, HelpDeskTicket 
from partenon.helpdesk.helpdesk import Status as StatusTickets


class FaveoTicketClose(viewsets.ViewSet):
    status_ticket = enums.StateEnums.ticket
    helpdesk_ticket_class = HelpDeskTicket
    helpdesk_status_class = HelpDesk.status 
    helpdesk_user_class = HelpDesk.user

    def create(self, request, *args, **kwargs):
        ticket_id = get_value_or_404(
            request.data, 'ticket_id', 'Not send ticket id')
        reason = get_value_or_404(
            request.data, 'reason', 'Not send reason to close')

        status_close = StatusTickets.get_by_name(
            self.status_ticket.closed)
        user = self.helpdesk_user_class.get('aplicaciones@puntacana.com')

        ticket = self.helpdesk_ticket_class.get_specific_ticket(ticket_id)
        ticket.add_note(reason, user)
        ticket.change_state(status_close)

        return Response({"success": 'ok'}, status.HTTP_200_OK)


class FaveoWebHookView(viewsets.ViewSet):
    model = ServiceRequest
    status = enums.StateEnums.service_request
    status_ticket = enums.StateEnums.ticket
    state_model = State
    permission_classes_by_action = {'create': [AllowAny]} 
    helpdesk_ticket_class = HelpDeskTicket
    helpdesk_status_class = HelpDesk.status 
    helpdesk_user_class = HelpDesk.user

    def re_open_ticket_and_note(self, service_request):
        ticket = self.helpdesk_ticket_class.get_specific_ticket(
            service_request.ticket_id)

        ticket_state_open = self.helpdesk_status_class.get_state_by_name(
            self.status_ticket.open)
        ticket.change_state(ticket_state_open)

        user = self.helpdesk_user_class.get('aplicaciones@puntacana.com')
        note = 'No se puede cerrar este ticket '\
               'sin antes cerrar el aviso número {}'.format(service_request.aviso_id)
        ticket.add_note(note, user)

    def closed_service_request(self, service_request):
        if service_request.aviso_id:
            self.re_open_ticket_and_note(service_request)
            body = {'message': 'Service Request has aviso create'}
            return body, status.HTTP_400_BAD_REQUEST 

        service_request.state, _ = self.state_model.objects.get_or_create(
            name=self.status.closed)
        service_request.save()
        body = {'success': 'ok', 'message': 'close service request'}
        return body, status.HTTP_200_OK
    
    def none_status(self, service_request):
        body = {'message': 'Not send valid status code'}
        return body, status.HTTP_200_OK

    def create(self, request, *args, **kwargs):
        if not request.data.get('event') == 'ticket_status_updated':
            return Response({}, 200)
        ticket_id = get_value_or_404(request.data, 'ticket[id]', 'Not send ticket id')

        status_id = get_value_or_404(request.data, 'ticket[status]', 'Not send ticket status key')
        status_faveo = StatusTickets.get_by_id(status_id)

        service_request = get_object_or_404(self.model, ticket_id=ticket_id)

        actions = {self.status_ticket.closed: self.closed_service_request}
        body, status = actions.get(status_faveo.name, self.none_status)(service_request)

        return Response(body, status)
    
    def get_permissions(self):
        try:
            # return permission_classes depending on `action` 
            permissions = self.permission_classes_by_action[self.action]
            return [permission() for permission in permissions]
        except KeyError: 
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]