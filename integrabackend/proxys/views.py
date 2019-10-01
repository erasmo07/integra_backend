from rest_framework import viewsets
from rest_framework.response import Response
from integrabackend.solicitude.views import get_value_or_404
from integrabackend.proxys import filters
from partenon.ERP import ERPClient, ERPResidents


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
            self.request.data,'email', 'Not send email')
        client_code = get_value_or_404(
            self.request.data, 'client_code', 'Not send client_code')

        erp_client = ERPClient(**{'code': client_code})
        return Response(erp_client.add_email(email)) 


class ERPResidentsViewSet(viewsets.ViewSet):
    filter_backends = (filters.ERPResidentsFilter, )
    erp_entity_class = ERPResidents

    def list(self, request, format=None):
        params = request.query_params.dict()
        kwargs = {
            "client_sap": params.get('client_sap'),
            "name": params.get('name')}
        erp_resident = self.erp_entity_class(**kwargs)
        return Response(erp_resident.search())