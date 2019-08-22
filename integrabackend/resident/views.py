from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action

from .models import Resident, Person, Property, PropertyType
from .serializers import (
    ResidentSerializer, PersonSerializer,
    PropertySerializer, PropertyTypeSerializer)


class ResidentCreateViewSet(viewsets.ModelViewSet):
    """
    Create resident
    """
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('email', 'id_sap')
    
    @action(detail=True, methods=['GET', 'POST'], url_path='property')
    def property(self, request, pk=None):
        resident = self.get_object()

        if request._request.method == 'GET':
            serializer = PropertySerializer(resident.properties.all(), many=True)
            return Response(serializer.data)
        
        if request._request.method == 'POST':
            properties_pks = request.data.get('properties') 
            properties = Property.objects.filter(pk__in=properties_pks)
            resident.properties.add(*properties)
            serializer = PropertySerializer(resident.properties.all(), many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        

class PersonViewSet(viewsets.ModelViewSet):
    """
    Create resident
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    """
    Crud property
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('id_sap',)

    def get_queryset(self, *args, **kwargs):
        all_property = super(PropertyViewSet, self).get_queryset(**kwargs)
        property_user = all_property.filter(resident__user=self.request.user)

        is_aplication = self.request.user.is_aplication
        return all_property if is_aplication else property_user 


class PropertyTypeViewSet(viewsets.ModelViewSet):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
