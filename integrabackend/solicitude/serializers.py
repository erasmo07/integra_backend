from rest_framework import serializers
from .models import Service, State, ServiceRequest
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


class ServiceRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceRequest
        fields = (
            'id', 'user', 'service',
            'service', 'state', 'client_sap',
            'note', 'creation_date', 'close_date',
            'phone', 'email', 'ownership', 'property')