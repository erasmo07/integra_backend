import coreapi
import coreschema
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.filters import BaseFilterBackend 
from partenon.ERP import ERPClient


class ClientInfoFilter(BaseFilterBackend):
    
    def get_schema_fields(self, view):
        client = coreapi.Field(
            name='client',
            location='query',
            required=True,
            type='number')
        return [client]


class ClientInfoViewSet(viewsets.ViewSet):
    filter_backends = (ClientInfoFilter, )
    
    def list(self, request, format=None):
        params = request.query_params.dict()
        body = {"I_CLIENTE": params.get('client')}
        try:
            client_info = ERPClient._client.post(ERPClient._info_url, body)
            return Response(client_info) 
        except Exception as error:
            response = Response({'message': str(error)}) 
            response.status_code = 404
            return response