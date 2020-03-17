from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_list_or_404

from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action

from .models import (
    Resident, Person, Property,
    PropertyType, TypeIdentification)
from .serializers import (
    ResidentSerializer, PersonSerializer,
    PropertySerializer, PropertyTypeSerializer,
    ResidentUserserializer, TypeIdenticationSerializer)


class ResidentCreateViewSet(viewsets.ModelViewSet):
    """
    Create resident
    """
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('email', 'id_sap')

    @action(detail=True, methods=['GET', 'POST', "DELETE"], url_path='property')
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