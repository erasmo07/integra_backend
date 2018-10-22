from django.shortcuts import render
from rest_framework import viewsets
from .models import Service, ServiceRequest, State
from .serializers import (
    ServiceSerializer, StateSerializer,
    ServiceRequestSerializer)
from .enums import StateEnums
from . import helpers


# Create your views here.
class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List type service
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer 



class StateSolicitudeServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List solicitud service's status
    """
    queryset = State.objects.filter(StateEnums.service_request.limit_choice)
    serializer_class = StateSerializer
    

class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    CRUD service request
    """
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer

    def perform_create(self, serializer):
        super(ServiceRequestViewSet, self).perform_create(serializer)
        helpers.process_to_create_service_request(serializer.instance)