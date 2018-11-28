from rest_framework import serializers
from .models import (
    Service, State, ServiceRequest,
    DateServiceRequested, Day, DayType, ScheduleAvailability,
    Quotation)
from ..users.serializers import UserSerializer
from ..resident.serializers import PropertySerializer


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


class QuotationSerializer(serializers.ModelSerializer):
    state = StateSerializer(read_only=True)

    class Meta:
        model = Quotation
        fields = ('file', 'state', 'note')
        read_only_fields = ('id', )


class ServiceRequestSerializer(serializers.ModelSerializer):
    date_service_request = DateServiceRequestSerializer()
    state = StateSerializer(read_only=True)
    quotation = QuotationSerializer(read_only=True)

    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'service', 'note', 'phone', 'email', 
            'property', 'date_service_request', 
            'require_quotation', 'state', 'quotation')

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


class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    date_service_request = DateServiceRequestSerializer()
    state = StateSerializer(read_only=True)
    quotation = QuotationSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    property = PropertySerializer()

    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'service', 'note', 'phone', 'email', 
            'property', 'date_service_request', 
            'require_quotation', 'state', 'quotation')