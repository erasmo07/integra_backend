from django.shortcuts import render
from rest_framework import viewsets
from . import models, serializers


class PaymentAttemptViewSet(viewsets.ModelViewSet):
    """
    Create resident
    """
    queryset = models.PaymentAttempt.objects.all()
    serializer_class = serializers.PaymentAttemptSerializer
