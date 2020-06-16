import json
import os

import requests
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import xmltodict
from integrabackend.proxys import filters
from integrabackend.solicitude import enums
from integrabackend.solicitude.views import get_value_or_404
from integrabackend.payment.models import Invoice
from integrabackend.payment.enums import StatusCompensation, StatusInvoices
from oraculo.gods.exceptions import BadRequest, NotFound, InternalServer
from oraculo.gods.faveo import APIClient as APIClientFaveo
from oraculo.gods.sita_db import APIClient as APIClientSitaDB
from oraculo.gods.sap import APIClient as APIClientERP
from partenon.ERP import ERPClient, ERPResidents
from partenon.helpdesk import HelpDesk


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
        params = request.query_params.dict()
        if not params:
            return Response({})

        client = self.api_client()
        return Response(client.get(self.proxy_url, params=params))

    def retrieve(self, request, pk=None):
        client = self.api_client()
        url = "%s%s/" % (self.proxy_url, pk)
        return Response(client.get(url))


class SitaFlightViewSet(viewsets.ViewSet):
    url = os.environ.get('SITAAMS_URL')
    token = os.environ.get('SITAAMS_TOKEN')
    _headers = {
        'Content-type': 'text/xml',
        'SOAPAction': os.environ.get("SITAAMS_ACTION")
    }
    

    def get_body(self, from_, to):
        return '''
            <soap:Envelope
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                <soap:Body>
                    <GetFlights xmlns="http://www.sita.aero/ams6-xml-api-webservice">
                    <sessionToken>{}</sessionToken>
                    <from>{}</from>
                    <to>{}</to>
                    <airport>PUJ</airport>
                    </GetFlights>
                </soap:Body>
            </soap:Envelope>
        '''.format(self.token, from_, to)

    def get_flight(self, data):
        keys = [
            's:Envelope', 's:Body', 'GetFlightsResponse',
            'GetFlightsResult', 'WebServiceResult',
            'ApiResponse', 'Data', 'Flights', 'Flight']
        for key in keys:
            data = data.get(key, {})
        return data

    def list(self, request):
        from_ = get_value_or_404(
            request.query_params.dict(),
            'from',
            'Not send from on query params')
        to = get_value_or_404(
            request.query_params.dict(),
            'to',
            'Not send to on query params'
        )
        body = self.get_body(from_, to)
        response = requests.post(self.url, data=body, headers=self._headers)
        return Response(self.get_flight(xmltodict.parse(response.content)))


class ERPClientViewSet(viewsets.ViewSet):
    erp_client_class = ERPClient

    @action(detail=True, methods=['GET'], url_path='invoices')
    def invoice(self, request, pk=None, format=None):
        try:
            erp_client = ERPClient(**dict(client_code=pk))
            
            params = request.query_params.dict()
            merchant = params.get('merchant', '')
            language = params.get('language', 'ES')

            invoices_sap = erp_client.invoices(merchant=merchant, language=language)

            invoices_not_compensated = Invoice.objects.filter(
                payment_attempt__sap_customer=pk,
                payment_attempt__status_compensation__name=StatusCompensation.not_compensated,
                status__name=StatusInvoices.not_compensated
            )

            for index, invoice in enumerate(invoices_sap):
                pending_compensated = invoices_not_compensated.filter(
                    document_number=invoice._base.get('document_number'))
                if not pending_compensated.exists():
                    continue
                invoices_sap.pop(index)

            return Response([invoice._base for invoice in invoices_sap])
        except NotFound as exception:
            return Response({}, status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['GET'], url_path='invoice-pdf')
    def invoice_pdf(self, request, pk=None, format=None):
        try:
            params = request.query_params.dict()

            document_number = get_value_or_404(
                params, 'document_number', 'Not send document_number')

            merchant = get_value_or_404(
                params, 'merchant', 'Not send merchant')

            language = params.get('language', 'S')

            erp_client = ERPClient(**dict(client_code=pk))

            invoice_pdf = erp_client.invoice_pdf(
                document_number, merchant, language=language)
            return Response({'binary': invoice_pdf.data})
        except NotFound as exception:
            return Response({}, status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['GET'], url_path='advance-payment')
    def advance_payment(self, request, pk=None, format=None):
        try:
            params = request.query_params.dict()

            merchant = get_value_or_404(
                params, 'merchant', 'Not send merchant'
            )
            
            erp_client = self.erp_client_class(**dict(client_code=pk))
            language = params.get('language', 'ES')

            advance_payments = erp_client.advance_payment(
                merchant=merchant, language=language)
            return Response(
                [advance_payment._base
                for advance_payment in advance_payments]
            )
        except NotFound as exception:
            return Response({}, status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['GET'], url_path='society')
    def society(self, request, pk=None, format=None):
        try:
            params = request.query_params.dict()

            merchant = get_value_or_404(
                params, 'merchant', 'Not send merchant')

            societies = APIClientERP().post(
                'api_portal_clie/dame_soc_mercha',
                {
                    'sap_customer': pk,
                    'merchant_number': merchant
                }
            )
            return Response(societies)
        except NotFound as exception:
            return Response({}, status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['GET'], url_path='account-status-pdf')
    def account_status_pdf(self, request, pk=None, format=None):
        try:
            params = request.query_params.dict()

            merchant = get_value_or_404(
                params, 'merchant', 'Not send merchant')
            date = get_value_or_404(
                params, 'date', 'Not send date')
            
            companies = request.query_params.getlist('companies', []) 
            companies = [{'bukrs': company} for company in companies]

            account_status = APIClientERP().post(
                'api_portal_clie/dame_estado_cue',
                {
                    "sap_customer": pk,
                    "lang": params.get('language', 'E'),
                    "I_MERCHANTNR": merchant,
                    "I_DATE": date,
                    "companies": companies
                } 
            )
            return Response(account_status)
        except NotFound as exception:
            return Response({}, status.HTTP_404_NOT_FOUND)


class TemporalInvoiceViewSet(viewsets.ViewSet):
    url = 'api_fact_vipcae/factura'
    
    def create(self, request, *args, **kwargs):
        try:
            return Response(
                APIClientERP().post(self.url, request.data.dict())
            )
        except (NotFound, BadRequest) as exception:
            error = dict(error=str(exception))
            return Response(error, status.HTTP_404_NOT_FOUND)


class ExchangeRateViewSet(viewsets.ViewSet):
    url = 'api_portal_clie/dolar_exchange'

    def list(self, request):
        try:
            return Response(
                APIClientERP().get(self.url)
            )
        except BadRequest as exception:
            error = dict(error=str(exception))
            return Response(error, status.HTTP_400_BAD_REQUEST)
        except InternalServer as exception:
            error = dict(error=str(exception))
            return Response(
                error,
                status.HTTP_500_INTERNAL_SERVER_ERROR)