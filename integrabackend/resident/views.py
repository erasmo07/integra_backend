from rest_framework import viewsets, mixins

from .models import Resident, Person
from .serializers import ResidentSerializer, PersonSerializer


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
