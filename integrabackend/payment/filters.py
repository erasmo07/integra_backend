import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from integrabackend.payment import models


class PaymentAttemptFilter(django_filters.FilterSet):
    to = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    from_ = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = models.PaymentAttempt
        fields = {
            'sap_customer': ['exact'],
            'invoices__status': ['exact'],
        }