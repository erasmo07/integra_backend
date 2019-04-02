from rest_framework import serializers
from .models import Resident, Person, Property, PropertyType


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


class ResidentSerializer(serializers.ModelSerializer):
    properties = PropertySerializer(read_only=True, many=True)

    class Meta:
        model = Resident
        fields = (
            'id', 'name', 'email',
            'telephone', 'sap_customer', 'user', 'properties', 'id_sap')
        read_only_fields = ('id',)


class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = ('id', 'name', 'email', 'identification', 'create_by',
                  'type_identification')
        read_only_fields = ('id', )
