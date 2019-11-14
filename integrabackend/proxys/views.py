import json
import os
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from integrabackend.solicitude.views import get_value_or_404
from integrabackend.solicitude import enums
from integrabackend.proxys import filters
from partenon.helpdesk import HelpDesk
from partenon.ERP import ERPClient, ERPResidents
from oraculo.gods.exceptions import NotFound, BadRequest
from oraculo.gods.faveo import APIClient as APIClientFaveo
from oraculo.gods.sita_db import APIClient as APIClientSitaDB


class ClientInfoViewSet(viewsets.ViewSet):
    filter_backends = (filters.ClientInfoFilter, )

    def list(self, request, format=None):
        params = request.query_params.dict()
        try:
            kwargs = {'client_number': params.get('client')}
            erp_client = ERPClient(**kwargs)
            return Response(erp_client.info())
        except Exception as error:
            response = Response({'message': str(error)})
            response.status_code = 404
            return response


class SearchClientViewSet(viewsets.ViewSet):
    filter_backends = (filters.SearchClientFilter, )

    def list(self, request, format=None):
        params = request.query_params.dict()
        try:
            kwargs = {
                'client_code': params.get('code'),
                'client_name': params.get('name')}
            erp_client = ERPClient(**kwargs)
            return Response(erp_client.search())
        except Exception as error:
            response = Response({'message': str(error)})
            response.status_code = 404
            return response


class ClientHasCreditViewSet(viewsets.ViewSet):
    filter_backends = (filters.SearchClientFilter, )

    def list(self, request, format=None):
        params = request.query_params.dict()
        try:
            kwargs = {'client_code': params.get('code')}
            erp_client = ERPClient(**kwargs)
            return Response(erp_client.has_credit())
        except Exception as error:
            response = Response({'message': str(error)})
            response.status_code = 400
            return response


class ClientAddEmailViewSet(viewsets.ViewSet):

    def create(self, request, *args, **kwargs):
        email = get_value_or_404(
            self.request.data, 'email', 'Not send email')
        client_code = get_value_or_404(
            self.request.data, 'client_code', 'Not send client_code')

        try:
            erp_client = ERPClient(**{'client_code': client_code})
            return Response(erp_client.add_email(email))
        except BadRequest as exception:
            message = json.loads(exception.args[0])
            return Response(message, status.HTTP_400_BAD_REQUEST)


class ERPResidentsViewSet(viewsets.ViewSet):
    filter_backends = (filters.ERPResidentsFilter, )
    erp_entity_class = ERPResidents

    def list(self, request, format=None):
        params = request.query_params.dict()
        kwargs = {
            "client_sap": params.get('client_sap'),
            "name": params.get('name')}
        try:
            erp_resident = self.erp_entity_class(**kwargs)
            return Response(erp_resident.search())
        except NotFound as exception:
            return Response({}, status.HTTP_404_NOT_FOUND)


class ERPResidentsPrincipalEmailViewSet(viewsets.ViewSet):
    filter_backends = (filters.ERPResidentsPrincipalEmailFilter, )
    erp_class = ERPResidents

    def list(self, request, format=None):
        email = get_value_or_404(
            request.query_params.dict(), 'email', 'Not send email')
        try:
            response = self.erp_class.get_principal_email(email)
            return Response(response, status.HTTP_200_OK)
        except NotFound:
            return Response({}, status.HTTP_404_NOT_FOUND)


class FaveoTicketDetailViewSet(viewsets.ViewSet):
    api_client = APIClientFaveo
    helpdesk_class = HelpDesk
    proxy_url = 'api/v1/helpdesk/ticket'
    admin_email = os.environ.get('FAVEO_ADMIN_EMAIL', None)
    status_ticket = enums.StateEnums.ticket

    def list(self, request):
        return Response({})

    def retrieve(self, request, pk=None):
        client = self.api_client()
        return Response(client.get(self.proxy_url, params={'id': pk}))
    
    @action(detail=True, methods=['POST'], url_path='thread')
    def add_internal_note(self, request, pk=None):
        note = get_value_or_404(self.request.data, 'note', 'note is required') 
        ticket = HelpDesk.ticket.get_specific_ticket(pk)
        admin_user = HelpDesk.user.get(self.admin_email)
        try:
            return Response(ticket.add_note(note, admin_user))
        except Exception as exception:
            message = json.loads(exception.args[0])
            return Response(message, status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['POST'], url_path='close')
    def close(self, request, pk=None):
        reason = get_value_or_404(
            request.data, 'reason', 'Not send reason to close')

        status_close = self.helpdesk_class.status.get_state_by_name(
            self.status_ticket.closed)
        user = self.helpdesk_class.user.get('aplicaciones@puntacana.com')

        ticket = self.helpdesk_class.ticket.get_specific_ticket(pk)
        ticket.add_note(reason, user)
        ticket.change_state(status_close)

        return Response({"success": 'ok'}, status.HTTP_200_OK)


class SitaDBDepartureFlightViewSet(viewsets.ViewSet):
    api_client = APIClientSitaDB
    proxy_url = 'api/v1/departure-flight/'

    def list(self, request):
        client = self.api_client()
        params = params=request.query_params.dict()
        if not params:
            return Response({})
        return Response(client.get(self.proxy_url, params=params))
    
    def retrieve(self, request, pk=None):
        client = self.api_client()
        url = "%s%s/" % (self.proxy_url, pk)
        return Response(client.get(url))