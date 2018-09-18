from rest_framework import viewsets, mixins
from .models import Resident
from .serializers import ResidentSerializer


class ResidentCreateViewSet(mixins.CreateModelMixin,
                            viewsets.GenericViewSet):
    """
    Create resident
    """
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
