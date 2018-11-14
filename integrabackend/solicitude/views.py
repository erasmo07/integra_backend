from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework import status
from .models import Service, ServiceRequest, State, Day
from .serializers import (
    ServiceSerializer, StateSerializer,
    ServiceRequestSerializer, DaySerializer)
from .enums import StateEnums
from . import helpers
from partenon.ERP import ERPAviso


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
    queryset = State.objects.filter(
        StateEnums.service_request.limit_choice)
    serializer_class = StateSerializer
    

class DayViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List day.
    """
    queryset = Day.objects.filter(active=True)
    serializer_class = DaySerializer


class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    CRUD service request
    """
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer

    def get_queryset(self):
        queryset = super(ServiceRequestViewSet, self).get_queryset()
        return queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        state_open, _ = State.objects.get_or_create(
            name=StateEnums.service_request.draft)
        serializer.save(
            user=self.request.user,
            state=state_open)
        helpers.process_to_create_service_request(serializer.instance)


class AvisoViewSet(viewsets.ViewSet):
    model = ServiceRequest

    def create(self, request):
        ticket_id = self.request.data.get('ticket_id')
        if not ticket_id:
            return Response(
                {'message': 'Not set ticket_id'}, status.HTTP_404_NOT_FOUND)

        service_request = self.model.objects.filter(ticket_id=ticket_id)
        if not service_request.exists():
            return Response(
                {'message': 'Not exists service request with it ticket_id'},
                status.HTTP_404_NOT_FOUND)

        try:
            helpers.process_to_create_aviso(service_request.first())
            return Response({'success': 'ok'}, status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({"message": str(ex)}, status.HTTP_404_NOT_FOUND)
    
    def list(self, request):
        params = request.query_params.dict()
        ticket_id = params.get('ticket_id')
        if not ticket_id:
            return Response(
                {'message': 'Not set ticket_id'},
                status.HTTP_404_NOT_FOUND)

        service_request = self.model.objects.filter(ticket_id=ticket_id)
        if not service_request.exists():
            return Response(
                {'message': 'Not exists service request with it ticket_id'},
                status.HTTP_404_NOT_FOUND)

        try:
            erp_aviso = ERPAviso()
            info = erp_aviso.info(aviso=service_request.first().aviso_id)
            return Response(info)
        except Exception as ex:
            return Response(
                {"message": str(ex)},
                status.HTTP_404_NOT_FOUND)

    def update(self, request, pk=None):
        state = request.data.get('state')
        if not state:
            return Response(
                {'message': 'Not set state'},
                status.HTTP_404_NOT_FOUND)

        service_request = self.model.objects.filter(aviso_id=pk)
        if not service_request.exists():
            return Response(
                {'message': 'Not exists service request with it PK'},
                status.HTTP_404_NOT_FOUND)
        
        if state == "RACU":
            helpers.notify_to_aprove_or_reject_service(service_request.first())
        return Response({'success': 'ok'}, status.HTTP_201_CREATED)