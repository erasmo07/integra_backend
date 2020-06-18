from rest_framework import serializers
from . import models, enums
from ..solicitude.serializers import DaySerializer
from ..resident.serializers import PersonSerializer
from ..resident.models import Property, Person
from collections import OrderedDict


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


class StatusInvitationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.StatusInvitation
        fields = '__all__'
        read_only_fields = ('id', )


class StatusInvitationESSerializer(StatusInvitationSerializer):
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
    

class TransportationSerializerDetail(serializers.ModelSerializer):

    class Meta:
        model = models.Transportation
        fields = '__all__'


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


class SupplierSerializerDetail(serializers.ModelSerializer):
    transportation = TransportationSerializerDetail()

    class Meta:
        model = models.Supplier
        fields = '__all__'


class TypeInvitationField(serializers.RelatedField):
    
    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        return models.TypeInvitation.objects.filter(id=data).first()


class PropertyField(serializers.RelatedField):

    def to_representation(self, value):
        return value.address
    
    def to_internal_value(self, data):
        return Property.objects.filter(id=data).first()


class InvitationSerializer(serializers.ModelSerializer):
    invitated = PersonSerializer()
    supplier = SupplierSerializer(required=False)
    type_invitation = TypeInvitationField(
        queryset=models.TypeInvitation.objects.all())
    status = serializers.SlugRelatedField(
        read_only=True, slug_field='name')

    class Meta:
        model = models.Invitation
        fields = (
            'id', 'type_invitation', 'date_entry',
            'date_out', 'invitated', 'note', 'number',
            'supplier', 'status', 'property', 'area', 'total_companions')
        read_only_fields = ('id', 'number', 'area')
        extra_kwargs = {'property': {'source': 'ownership'}}
    
    def validate(self, data):
        supplier = enums.TypeInvitationEnums.supplier
        is_supplier = data.get('type_invitation') == supplier
        if is_supplier and not data.get('supplier'):
            raise serializers.ValidationError(
                'supplier field is required for supplier invitation')
        return data
        
    
    def create(self, validated_data):
        invitated = validated_data.pop('invitated', None)
        supplier = validated_data.pop('supplier', None)

        if invitated:
            type_identification = invitated.pop('type_identification')
            invitated['type_identification'] = str(type_identification.id)

            serializer = PersonSerializer(data=invitated)
            serializer.is_valid(raise_exception=True)

            person = serializer.save(create_by=self.context.get('request').user)
            validated_data['invitated_id'] = person.id

        invitation = super(InvitationSerializer, self).create(validated_data)
        
        if supplier:
            serializer = SupplierSerializer(data=supplier)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            invitation.supplier = serializer.instance
            invitation.save()

        return invitation

    def update(self, instance, validated_data):
        invitated = validated_data.pop('invitated', [])
        supplier = validated_data.pop('supplier', None)

        for attribute in [
            'date_entry', 'date_out', 'ownership',
                'total_companions', 'note', 'type_invitation']:
            setattr(
                instance,
                attribute,
                validated_data.get(
                    attribute, getattr(instance, attribute)))
        instance.save()

        type_identification = invitated.pop('type_identification')
        invitated['type_identification'] = str(type_identification.id)

        serializer = PersonSerializer(instance=instance.invitated, data=invitated)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if supplier:
            serializer = SupplierSerializer(data=supplier)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            instance.supplier = serializer.instance
            instance.save()

        return instance


class InvitationSerializerDetail(serializers.ModelSerializer):
    invitated = PersonSerializer(required=False)
    supplier = SupplierSerializerDetail(required=False)

    class Meta:
        model = models.Invitation
        fields = [
            'type_invitation',
            'invitated',
            'property',
            'date_entry',
            'date_out',
            'note',
            'supplier',
            'total_companions',
        ]

        extra_kwargs = {
            'property': {'source': 'ownership'},
        }

    def to_representation(self, instance):
        result = super(
            InvitationSerializerDetail, self
        ).to_representation(instance)
        return OrderedDict(
            [(key, result[key])
            for key in result
            if result[key] is not None])


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


class PersonUpdateCheckinSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = ['name', 'type_identification', 'identification']


class CheckInSerializer(serializers.ModelSerializer):
    invitation = serializers.UUIDField(required=False)
    guest = PersonUpdateCheckinSerializer(required=True)
    persons = PersonSerializer(many=True, required=False)
    terminal = serializers.PrimaryKeyRelatedField(
        queryset=models.Terminal.objects.all(),
        required=True
    )
    transport = TransportationSerializer()
    
    class Meta:
        model = models.CheckIn
        fields = "__all__"
        read_only = (
            'id', 'invitation', 'user', 'date')

    def create(self, validated_data):
        persons = validated_data.pop('persons', [])
        validated_data['transport'] = models.Transportation.objects.get_or_create(
            **validated_data.pop('transport')
        )[0]

        guest = validated_data.pop('guest')

        invitation = validated_data.get('invitation')
        
        for attribute in PersonUpdateCheckinSerializer.Meta.fields:
            setattr(
                invitation.invitated,
                attribute,
                guest.get(attribute, getattr(invitation.invitated, attribute)))
        invitation.invitated.save()

        validated_data['guest'] = invitation.invitated

        check_in = self.Meta.model.objects.create(**validated_data)

        for person in persons:
            instance = Person.objects.filter(**person)
            if instance.exists():
                check_in.persons.add(instance.first())
            else:
                person['create_by_id'] = check_in.user.id
                check_in.persons.add(Person.objects.create(**person))
        return check_in