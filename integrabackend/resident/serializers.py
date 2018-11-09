from rest_framework import serializers
from .models import Resident, Person, Property


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


class PropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = Property
        fields = ('id', 'name')
        read_only_fields = ('id', )