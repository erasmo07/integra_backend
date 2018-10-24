from rest_framework import viewsets, mixins

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
    