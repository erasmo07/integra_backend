from rest_framework import serializers
from .models import Invitation, TypeInvitation


class InvitationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invitation
        fields = ('id', 'resident', 'type_invitation',
                  'date_entry', 'date_out', 'invitated')
        read_only_fields = ('id', )


class TypeInvitationSerializer(serializers.ModelSerializer):

    class Meta:
        model = TypeInvitation
        fields = ('id', 'name')
        read_only_fields = ('id', )
