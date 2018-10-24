from rest_framework import serializers
from .models import (
    Service, State, ServiceRequest,
    DateServiceRequested, Day)
from ..users.serializers import UserSerializer


class ServiceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Service 
        fields = ('id', 'name')
        read_only_fields = ('id', )


class StateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = State 
        fields = ('id', 'name')
        read_only_fields = ('id', )


class DaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Day
        fields = ('id', 'name')
        read_only_fields = ('id', )


class DateServiceRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = DateServiceRequested 
        fields = ('id', 'day', 'checking', 'checkout',)
        read_only_fields = ('id', )


class ServiceRequestSerializer(serializers.ModelSerializer):
    date_service_request = DateServiceRequestSerializer()

    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'service', 'client_sap',
            'note', 'creation_date', 'phone',
            'email', 'ownership', 'property',
            'date_service_request')
    
    def create(self, validated_data):
        date_service_request = validated_data.pop('date_service_request')
        days = date_service_request.pop('day')
        date_service_request = DateServiceRequested.objects.create(
            **date_service_request)
        date_service_request.day.add(*days)
        date_service_request.save()
        service_request = ServiceRequest.objects.create(
            date_service_request=date_service_request,
            **validated_data)
        return service_request 