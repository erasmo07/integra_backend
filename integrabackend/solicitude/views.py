from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from oraculo.gods.sap import APIClient as APISap
from partenon.ERP import ERPAviso, ERPClient
from partenon.ERP.exceptions import NotHasOrder
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound
from rest_framework.response import Response

from . import helpers, tasks
from .enums import StateEnums
from .models import Day, Service, ServiceRequest, State
from .paginates import ServiceRequestPaginate
from .permissions import HasCreditPermission
from .serializers import (DaySerializer, ServiceEnSerializer,
                          ServiceRequestDetailSerializer, ServiceRequestFaveo,
                          ServiceRequestSerializer, ServiceSerializer,
                          StateSerializer)

from integrabackend.resident.serializers import ResidentSerializer
from integrabackend.contrib import enums
from integrabackend.message.models import Message
from integrabackend.message.serializers import MessageSerializer


class Http500(APIException):
    status_code = 500


def get_value_or_404(data, key_value, message):
    if not data.get(key_value):
        raise NotFound(detail=message)
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
    

class ServiceAPPViewSet(viewsets.ViewSet):
    serializer_resident = ResidentSerializer
    serializer_service = ServiceSerializer
    model_service = Service

    def get_serializer_context(self, *args, **kwargs):
        return {
            'request': self.request,
            'view': self,
        }
    
    def get_queryset(self):
        _property = self.request.query_params.get('property', None)

        queryset = self.model_service.objects.all()
        if _property:
            return queryset.filter(
                projectservice__project__property__pk=_property)
        return queryset

    def get_services_and_message(self):
        if not hasattr(self.request.user, 'resident'):
            return '', []

        resident = self.serializer_resident(
            instance=self.request.user.resident,
            context=self.get_serializer_context())

        if not resident.data.get('sap_customer'):
            return '', []

        queryset = self.get_queryset() 

        kwargs = { 'client_code': resident.data.get('sap_customer')}
        erp_client = ERPClient(**kwargs)
        if not erp_client.has_credit().get('puede_consumir'):
            code = enums.MessageCode.not_has_credit
            instance = Message.objects.get_or_create(code=code)
            message = MessageSerializer(
                instance=instance, context={'request': self.request}) 
            return message.data.get('message'), queryset.filter(skip_credit_validation=True)

        return '', queryset

    def list(self, request, *args, **kwargs):
        msg, services = self.get_services_and_message()

        serializer_service = self.serializer_service(services, many=True)
        data = {'service': serializer_service.data, 'message': msg}
        return Response(data)
    

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
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filter_fields = ['ticket_id',]
    ordering_fields = ['ticket_id', 'service', 'state', 'creation_date']
    permission_classes = (HasCreditPermission, )

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
        tasks.create_service_request.delay(str(serializer.instance.id))

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
    def faveo(self, request):
        serializer = ServiceRequestFaveo(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create_faveo(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=["GET"], url_path='search-by-invoice')
    def search_by_invoice(self, request):
        data = request.query_params.dict()
        get_value_or_404(data, 'invoice','Not set invoice')
        data['numero_factura'] = data.pop('invoice')

        url_sap = 'api_portal_clie/dame_dato_factu'
        response = APISap().get(url_sap, params=data)

        instances = ServiceRequest.objects.filter(
            aviso_id=response.get('aviso'))
        serializer = ServiceRequestDetailSerializer(instances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
                return Response(body, status.HTTP_400_BAD_REQUEST)

        action = {
            self.states.requires_quote_approval: helpers.client_valid_quotation,
            self.states.requires_acceptance_closing: helpers.client_valid_work}
        state = get_value_or_404(request.data, 'state', 'Not set state')
        try:
            action.get(state)(service_request)
            return Response({'success': 'ok'}, status.HTTP_200_OK)
        except NotHasOrder as error:
            return Response({'error': str(error)}, status.HTTP_404_NOT_FOUND)
