import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from integrabackend.payment import models


class PaymentAttemptFilter(django_filters.FilterSet):
    date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = models.PaymentAttempt
        fields = {
            'sap_customer': ['exact'],
            'status': ['exact'],
            'merchant_number': ['exact'],
        }