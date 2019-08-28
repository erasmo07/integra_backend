from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, get_object_or_404
from ..solicitude.models import ServiceRequest, State
from ..solicitude import enums
from integrabackend.solicitude.views import get_value_or_404
from partenon.helpdesk import HelpDesk, HelpDeskTicket 
from partenon.helpdesk.helpdesk import Status as StatusTickets



class FaveoWebHookView(viewsets.ViewSet):
    model = ServiceRequest
    status = enums.StateEnums.service_request
    status_ticket = enums.StateEnums.ticket
    state_model = State

    def re_open_ticket_and_note(self):
        ticket_id = get_value_or_404(ticket_data, 'id', 'Not send ticket id')
        ticket = HelpDeskTicket.get_specific_ticket(ticket_id)

        ticket_state_close = StatusTickets.get_state_by_name(
            self.status_ticket.open)
        ticket.change_state(ticket_state_close)

        user = HelpDesk.user.get('admin@puntacana.com')
        note = "No se puede cerrar este ticket por que tiene un aviso creado"
        ticket.add_note(note, user)

    def closed_service_request(self, service_request):
        if service_request.aviso_id:
            self.re_open_ticket_and_note()
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
        ticket_data = request.data.get('ticket', {})
        ticket_id = get_value_or_404(ticket_data, 'id', 'Not send ticket id')

        states = get_value_or_404(
            ticket_data, 'statuses', 'Not send ticket status key')

        state_name = get_value_or_404(states, 'name', 'Not resive status name') 
        service_request = get_object_or_404(self.model, ticket_id=ticket_id)

        actions = {self.status_ticket.closed: self.closed_service_request}
        body, status = actions.get(state_name, self.none_status)(service_request)

        return Response(body, status)