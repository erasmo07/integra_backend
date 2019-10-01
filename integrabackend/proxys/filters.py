import coreapi
import coreschema
from rest_framework.filters import BaseFilterBackend 


class ClientInfoFilter(BaseFilterBackend):
    
    def get_schema_fields(self, view):
        client = coreapi.Field(
            name='client', location='query',
            required=True, type='number')
        return [client]


class SearchClientFilter(BaseFilterBackend):
    
    def get_schema_fields(self, view):
        client = coreapi.Field(
            name='code', location='query',
            required=True, type='number')
        name = coreapi.Field(
            name='name', location='query',
            required=True, type='string')
        return [client, name, client_sap]


class ERPResidentsFilter(BaseFilterBackend):
    
    def get_schema_fields(self, view):
        name = coreapi.Field(
            name='name',location='query',
            required=True, type='string')
        client_sap = coreapi.Field(
            name='client_sap',location='query',
            required=True,type='string')
        return [name, client_sap]
