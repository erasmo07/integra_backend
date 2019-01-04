from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action

from .models import Resident, Person, Property
from .serializers import (
    ResidentSerializer, PersonSerializer,
    PropertySerializer)


class ResidentCreateViewSet(viewsets.ModelViewSet):
    """
    Create resident
    """
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    
    @action(detail=True, methods=['GET', 'POST'], url_path='property')
    def property(self, request, pk=None):
        resident = self.get_object()

        if request._request.method == 'GET':
            serializer = PropertySerializer(resident.properties.all(), many=True)
            return Response(serializer.data)
        
        if request._request.method == 'POST':
            serializer = PropertySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            resident.properties.add(serializer.instance)
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

    def get_queryset(self, *args, **kwargs):
        queryset = super(PropertyViewSet, self).get_queryset(**kwargs)
        return queryset.filter(resident__user=self.request.user)
