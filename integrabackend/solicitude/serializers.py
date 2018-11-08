from rest_framework import serializers
from .models import (
    Service, State, ServiceRequest,
    DateServiceRequested, Day, DayType, ScheduleAvailability)
from ..users.serializers import UserSerializer


class ServiceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Service 
        fields = (
            'id', 'name', 'scheduled',
            'generates_invoice', 'requires_approval')
        read_only_fields = ('id', )


class StateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = State 
        fields = ('id', 'name')
        read_only_fields = ('id', )


class ScheduleAvailabilitySerializer(serializers.ModelSerializer):

    class Meta:
        model = ScheduleAvailability
        fields = ('start_time', 'end_time', 'msg_display')
        read_only_fields = ('id', )
        

class DayTypeSerializer(serializers.ModelSerializer):
    schedule_availability = ScheduleAvailabilitySerializer(read_only=True)

    class Meta:
        model = DayType
        fields = (
            'id', 'name', 'holiday',
            'schedule_availability')
        read_only_fields = ('id', )


class DaySerializer(serializers.ModelSerializer):
    day_type = DayTypeSerializer(read_only=True)

    class Meta:
        model = Day
        fields = ('id', 'name', 'day_type')
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
            'id', 'service', 'sap_customer',
            'note', 'creation_date', 'phone',
            'email', 'property', 'date_service_request')
    
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