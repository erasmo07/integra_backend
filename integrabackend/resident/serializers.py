from django.contrib.auth import get_user_model

from rest_framework import serializers
from .models import (
    Resident, Person, Property,
    PropertyType, TypeIdentification)


class TypeIdenticationSerializer(serializers.ModelSerializer):

    class Meta:
        model = TypeIdentification 
        fields = ('id', 'name')
        read_only_fields = ('id', )


class PropertyTypeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PropertyType
        fields = ('id', 'name')
        read_only_fields = ('id', )


class PropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = Property
        fields = (
            "id", "id_sap", "name", "address",
            "property_type", "street", "number", 'direction')
        read_only_fields = ('id', 'direction')


class ResidentUserserializer(serializers.ModelSerializer):
    
    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name',
            'last_login', 'date_joined')
        read_only_fields = ('id', 'last_login', 'date_joined')


class ResidentSerializer(serializers.ModelSerializer):
    properties = PropertySerializer(read_only=True, many=True)
    user = ResidentUserserializer(read_only=True)


    class Meta:
        model = Resident
        fields = (
            'id', 'name', 'email',
            'telephone', 'sap_customer',
            'user', 'properties', 'id_sap')
        read_only_fields = ('id',)
    
    def create(self, validated_data):
        request_data = self.context.get('request')
        if request_data and 'user' in request_data.data:
            validated_data.update(dict(user_id=request_data.data.get('user')))
        return super(ResidentSerializer, self).create(validated_data)


class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = ('id', 'name', 'email', 'identification',
                  'type_identification', 'create_by')
        read_only_fields = ('id', )


