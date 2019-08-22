from django.shortcuts import render, get_object_or_404
from django.http import Http404
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend
from .models import Service, ServiceRequest, State, Day
from .paginates import ServiceRequestPaginate
from .serializers import (
    ServiceSerializer, ServiceEnSerializer, StateSerializer,
    ServiceRequestSerializer, ServiceRequestDetailSerializer,
    DaySerializer, ServiceRequestFaveo)
from .enums import StateEnums
from . import helpers, tasks
from partenon.ERP import ERPAviso
from partenon.ERP.exceptions import NotHasOrder


class Http500(APIException):
    status_code = 500


def get_value_or_404(data, key_value, message):
    if not data.get(key_value):
        raise Http404(message)
    return data.get(key_value)


# Create your views here.
class ServiceViewSet(viewsets.ModelViewSet):
    """
    List type service
    """
    queryset = Service.objects.all()

    def get_serializer_class(self):
        serializer_language = dict(en=ServiceEnSerializer)
        language = self.request.META.get('HTTP_ACCEPT_LANGUAGE') 
        return serializer_language.get(language, ServiceSerializer)

    def get_queryset(self):
        _property = self.request.query_params.get('property', None)
        if _property:
            return super(ServiceViewSet, self).get_queryset().filter(
                projectservice__project__property__pk=_property)
        return super(ServiceViewSet, self).get_queryset()
    


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
    pagination_class = ServiceRequestPaginate
    filter_backends = (DjangoFilterBackend,)
    ordering = ('-creation_date',)
    filter_fields = ('ticket_id',)

    def get_queryset(self):
        queryset = super(ServiceRequestViewSet, self).get_queryset()
        if self.request.user.is_aplication:
            return queryset
        return queryset.filter(user=self.request.user)
    
    def get_serializer_class(self):
        serializer_class = {
            'list': ServiceRequestDetailSerializer,
            'retrieve': ServiceRequestDetailSerializer}
        return serializer_class.get(self.action, self.serializer_class) 

    def perform_create(self, serializer):
        state_open, _ = State.objects.get_or_create(
            name=StateEnums.service_request.draft)

        serializer.save(
            user=self.request.user,
            state=state_open)
        tasks.create_service_request.delay(str(serializer.instance.id))
    
    def perform_create_faveo(self, serializer):
        state_open, _ = State.objects.get_or_create(
            name=StateEnums.service_request.draft)
        serializer.save(state=state_open)

    @action(detail=True, methods=['POST'], url_path='approve-quotation')
    def aprove_quotation(self, request, pk=None):
        try:
            helpers.aprove_quotation(self.get_object())
        except ServiceRequest.quotation.RelatedObjectDoesNotExist:
            message = "ServiceRequest %s hasn't quotation" % pk
            return Response({'message': message}, status.HTTP_404_NOT_FOUND)
        return Response({'success': 'ok'}, status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='reject-quotation')
    def reject_quotation(self, request, pk=None):
        helpers.reject_quotation(self.get_object())
        return Response({'success': 'ok'}, status.HTTP_200_OK)
    
    @action(detail=True, methods=["POST"], url_path='approve-work')
    def approve_work(self, request, pk=None):
        helpers.approve_work(self.get_object())
        return Response({'success': 'ok'}, status.HTTP_200_OK)
    
    @action(detail=True, methods=['POST'], url_path='reject-work')
    def reject_work(self, request, pk=None):
        helpers.reject_work(self.get_object())
        return Response({'success': 'ok'}, status.HTTP_200_OK)
    
    @action(detail=False, methods=["POST"], url_path='faveo')
    def create_faveo(self, request):
        serializer = ServiceRequestFaveo(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create_faveo(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AvisoViewSet(viewsets.ViewSet):
    model = ServiceRequest
    states = StateEnums.aviso

    def create(self, request):
        ticket_id = get_value_or_404(
            self.request.data,
            'ticket_id', 'Not set ticket_id')

        service_request = get_object_or_404(self.model, ticket_id=ticket_id)
        try:
            helpers.process_to_create_aviso(service_request)
            return Response({'success': 'ok'}, status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({"message": str(ex)}, status.HTTP_404_NOT_FOUND)

    def list(self, request):
        data = request.query_params.dict()
        ticket_id = get_value_or_404(data, 'ticket_id','Not set ticket_id')
        service_request = get_object_or_404(self.model, ticket_id=ticket_id)
        try:
            erp_aviso = ERPAviso()
            info = erp_aviso.info(aviso=service_request.aviso_id)
            return Response(info)
        except Exception as ex:
            return Response(
                {"message": str(ex)},
                status.HTTP_404_NOT_FOUND)

    def update(self, request, pk=None):
        service_request = get_object_or_404(self.model, aviso_id=pk)

        if 'client' in request.data:
            try:
                client = request.data.get('client')
                helpers.change_aviso_client(pk, client)
                return Response({'success': 'ok'}, status.HTTP_200_OK)
            except Exception as exception:
                body = {'error': str(exception)}
                return Response(body, status.HTTP_404_NOT_FOUND)

        action = {
            self.states.requires_quote_approval: helpers.client_valid_quotation,
            self.states.requires_acceptance_closing: helpers.client_valid_work}
        state = get_value_or_404(request.data, 'state', 'Not set state')
        try:
            action.get(state)(service_request)
            return Response({'success': 'ok'}, status.HTTP_200_OK)
        except NotHasOrder as error:
            return Response({'error': str(error)}, status.HTTP_404_NOT_FOUND)