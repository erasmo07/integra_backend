from rest_framework import serializers
from .models import Invitation, TypeInvitation
from ..resident.serializers import PersonSerializer


class InvitationSerializer(serializers.ModelSerializer):
    invitated = PersonSerializer(many=True)

    class Meta:
        model = Invitation
        fields = ('id', 'resident', 'type_invitation',
                  'date_entry', 'date_out', 'invitated')
        read_only_fields = ('id', )
    
    def create(self, validated_data):
        invitateds = validated_data.pop('invitated')
        invitation = super(InvitationSerializer, self).create(validated_data)
        
        for invitated in invitateds:
            type_identification = invitated.pop('type_identification')
            invitated['type_identification'] = str(type_identification.id)

            serializer = PersonSerializer(data=invitated)
            serializer.is_valid(raise_exception=True)

            serializer.save(create_by=invitation.resident)
            invitation.invitated.add(serializer.instance)

        return invitation


class TypeInvitationSerializer(serializers.ModelSerializer):

    class Meta:
        model = TypeInvitation
        fields = ('id', 'name')
        read_only_fields = ('id', )
