from rest_framework import serializers
from .models import Resident, Person, Property, PropertyType


class ResidentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Resident
        fields = (
            'id', 'name', 'email',
            'telephone', 'sap_customer', 'user')
        read_only_fields = ('id', 'sap_customer')


class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = ('id', 'name', 'email', 'identification', 'create_by',
                  'type_identification')
        read_only_fields = ('id', )


class PropertyTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PropertyType
        fields = ('id', 'name')
        read_only_fields = ('id', )

class PropertySerializer(serializers.ModelSerializer):
    property_type = PropertyTypeSerializer(read_only=True)

    class Meta:
        model = Property
        fields = (
            'id', 'name', 'property_type',
            'address', 'street', 'number')
        read_only_fields = ('id', )
