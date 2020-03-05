from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin


from . import models, serializers, mixins


class InvitationViewSet(viewsets.ModelViewSet):
    """
    CRUD Invitation
    """
    queryset = models.Invitation.objects.all()
    serializer_class = serializers.InvitationSerializer

    def perform_create(self, serializer):
        serializer.save(create_by=self.request.user)


class TypeInvitationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List type invitation
    """
    queryset = models.TypeInvitation.objects.all()
    serializer_class = serializers.TypeInvitationSerializer


class MedioViewSet(
        mixins.ModelTranslateMixin,
        viewsets.ReadOnlyModelViewSet):
    """
    List medio
    """
    queryset = models.Medio.objects.all()
    serializer_class = serializers.MedioSerializer
    serializer_language = dict(
        en=serializers.MedioSerializer,
        es=serializers.MedioESSerializer
    )


class ColorViewSet(
        mixins.ModelTranslateMixin,
        viewsets.ReadOnlyModelViewSet):
    """
    List color 
    """
    queryset = models.Color.objects.all()
    serializer_class = serializers.ColorSerializer
    serializer_language = dict(
        en=serializers.ColorSerializer,
        es=serializers.ColorESSerializer)