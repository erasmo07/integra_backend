from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
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
            response = Response({'message': 'Not set ticket_id'})
            response.status_code = 404
            return response

        service_request = self.model.objects.filter(ticket_id=ticket_id)
        if not service_request.exists():
            response = Response(
                {'message': 'Not exists service request with it ticket_id'})
            response.status_code = 404
            return response

        try:
            helpers.process_to_create_aviso(service_request.first())
            return Response({'success': 'ok'})
        except Exception as ex:
            response = Response({"message": str(ex)})
            response.status_code = 404
            return response
    
    def list(self, request):
        params = request.query_params.dict()
        ticket_id = params.get('ticket_id')
        if not ticket_id:
            response = Response({'message': 'Not set ticket_id'})
            response.status_code = 404
            return response

        service_request = self.model.objects.filter(ticket_id=ticket_id)
        if not service_request.exists():
            response = Response(
                {'message': 'Not exists service request with it ticket_id'})
            response.status_code = 404
            return response

        erp_aviso = ERPAviso()
        info = erp_aviso.info(service_request.first().aviso_id)
        return Response(info)


    def update(self, request, pk=None):
        state = request.data.get('state')
        if not state:
            response = Response(
                {'message': 'Not set state'})
            response.status_code = 404
            return response

        service_request = self.model.objects.filter(aviso_id=pk)
        if not service_request.exists():
            response = Response(
                {'message': 'Not exists service request with it PK'})
            response.status_code = 404
            return response
        
        if state == "RACU":
            helpers.notify_to_aprove_or_reject_service(service_request.first())
        return Response({'success': 'ok'})