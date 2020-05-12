from django_filters.rest_framework import DjangoFilterBackend
from django.core.mail import send_mail
from django.shortcuts import get_list_or_404, get_object_or_404
from django.template.loader import get_template
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm

from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action

from .models import (
    Resident, Person, Property,
    PropertyType, TypeIdentification, Area)
from .serializers import (
    ResidentSerializer, PersonSerializer,
    PropertySerializer, PropertyTypeSerializer,
    ResidentUserserializer, TypeIdenticationSerializer,
    AreaSerializer)
from integrabackend.users.models import Application


class ResidentCreateViewSet(viewsets.ModelViewSet):
    """
    Create resident
    """
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('email', 'id_sap', 'sap_customer')
    form_reset_class = PasswordResetForm

    @action(detail=True, methods=['GET', 'POST', "DELETE"], url_path='property')
    def property(self, request, pk=None):
        resident = self.get_object()

        if request._request.method == 'GET':
            serializer = PropertySerializer(resident.properties.all(), many=True)
            return Response(serializer.data)

        if request._request.method == 'POST':
            properties_pks = request.data.getlist('properties')
            properties = Property.objects.filter(pk__in=properties_pks)
            resident.properties.add(*properties)
            serializer = PropertySerializer(resident.properties.all(), many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request._request.method == "DELETE":
            properties_pks = request.data.get('properties')
            properties = get_list_or_404(Property, pk__in=properties_pks)
            resident.properties.remove(*properties)

            return Response({"success": True}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST", 'PUT'], url_path='user')
    def add_user(self, request, pk=True):
        resident = self.get_object()

        if request._request.method == 'POST':
            if resident.user:
                error = {'message': "This resident has user"}
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

            serializer = ResidentUserserializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            resident.user = serializer.instance
            resident.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if request._request.method == "PUT":
            serializer = ResidentUserserializer(
                resident.user, data=request.data)
            serializer.is_valid(raise_exception=True)

            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["POST", 'PUT'], url_path='access')
    def access(self, request, pk=True):
        resident = self.get_object()

        if not request.user.is_aplication:
            return Response(
                'Cant assign application to user',
                status=status.HTTP_403_FORBIDDEN)
        
        if not resident.user:
            error = {'message': "This resident hasn't user"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        if request._request.method == 'POST':
            applications = get_list_or_404(
                Application, id__in=request.data.getlist('applications'))
            
            for application in applications:
                resident.user.accessapplication_set.create(
                    application=application)
            return Response({}, status=status.HTTP_200_OK)
        return Response({}, status.HTTP_400_BAD_REQUEST)


class PersonViewSet(viewsets.ModelViewSet):
    """
    Create resident
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('create_by',)

    def get_queryset(self):
        all_person = super(PersonViewSet, self).get_queryset()
        person_user = all_person.filter(create_by=self.request.user)

        return all_person if self.request.user.is_aplication else person_user
    

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

        return all_property if self.request.user.is_aplication else property_user


class PropertyTypeViewSet(viewsets.ModelViewSet):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = '__all__'


class TypeIdentificationViewSet(viewsets.ModelViewSet):
    queryset = TypeIdentification.objects.all()
    serializer_class = TypeIdenticationSerializer


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_fields = '__all__'