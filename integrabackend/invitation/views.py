from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin


from .models import Invitation, TypeInvitation
from .serializers import InvitationSerializer, TypeInvitationSerializer


class InvitationViewSet(viewsets.ModelViewSet):
    """
    CRUD Invitation
    """
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer

    def perform_create(self, serializer):
        serializer.save(create_by=self.request.user)


class TypeInvitationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List type invitation
    """
    queryset = TypeInvitation.objects.all()
    serializer_class = TypeInvitationSerializer
