from rest_framework import serializers
from . import models, enums
from ..solicitude.serializers import DaySerializer
from ..resident.serializers import PersonSerializer


class MedioSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.Medio
        fields = ('name', 'id')
        read_only_fields = ('id', )


class MedioESSerializer(MedioSerializer):
    name = serializers.CharField(source='name_es')


class ColorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.Color
        fields = ['name', 'id']
        read_only_fields = ('id', )


class ColorESSerializer(ColorSerializer):
    name = serializers.CharField(source='name_es')


class TransportationSerializer(serializers.ModelSerializer):
    color = serializers.UUIDField()
    medio = serializers.UUIDField()

    class Meta:
        model = models.Transportation
        fields = '__all__'
        read_only_fields = ('id', )
    
    def create(self, validated_data):
        validated_data['color_id'] = str(validated_data.pop('color'))
        validated_data['medio_id'] = str(validated_data.pop('medio'))
        instance, _ = self.Meta.model.objects.get_or_create(**validated_data)
        return instance
    

class SupplierSerializer(serializers.ModelSerializer):
    transportation = TransportationSerializer()

    class Meta:
        model = models.Supplier
        fields = '__all__'
        read_only_fields = ('id', )
    
    def create(self, validated_data):
        transportation = validated_data.pop('transportation', None)

        serializer = TransportationSerializer(data=transportation)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        validated_data.update(dict(transportation=serializer.instance))
        return super(SupplierSerializer, self).create(validated_data)   


class InvitationSerializer(serializers.ModelSerializer):
    invitated = PersonSerializer(many=True, required=False)
    supplier = SupplierSerializer(required=False)

    class Meta:
        model = models.Invitation
        fields = (
            'id', 'type_invitation', 'date_entry',
            'date_out', 'invitated', 'note', 'number',
            'supplier')
        read_only_fields = ('id', 'number')
    
    def validate(self, data):
        supplier = enums.TypeInvitationEnums.supplier
        is_supplier = data.get('type_invitation').name == supplier
        if is_supplier and not data.get('supplier'):
            raise serializers.ValidationError(
                'supplier field is required for supplier invitation')
        return data
        
    
    def create(self, validated_data):
        invitateds = validated_data.pop('invitated', [])
        supplier = validated_data.pop('supplier', None)
        invitation = super(InvitationSerializer, self).create(validated_data)
        
        for invitated in invitateds:
            type_identification = invitated.pop('type_identification')
            invitated['type_identification'] = str(type_identification.id)

            serializer = PersonSerializer(data=invitated)
            serializer.is_valid(raise_exception=True)

            serializer.save(create_by=invitation.create_by)
            invitation.invitated.add(serializer.instance)
        
        if supplier:
            serializer = SupplierSerializer(data=supplier)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            invitation.supplier = serializer.instance
            invitation.save()

        return invitation

    def update(self, instance, validated_data):
        invitateds = validated_data.pop('invitated', [])
        supplier = validated_data.pop('supplier', None)

        for attribute in ['date_entry', 'date_out', 'note']:
            setattr(
                instance,
                attribute,
                validated_data.get(
                    attribute, getattr(instance, attribute)))

        instance.save()
        return instance


class TypeInvitationProyectSerializer(serializers.ModelSerializer):
    not_available_days = DaySerializer(read_only=True, many=True)

    class Meta:
        model = models.TypeInvitationProyect
        exclude = ['type_invitation', 'id', 'project']


class TypeInvitationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TypeInvitation
        fields = ['name', 'id',]
        read_only_fields = ('id',)



