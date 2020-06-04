import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from integrabackend.resident import models


class ResidentFilter(django_filters.FilterSet):

    class Meta:
        model = models.Resident
        fields = ['email', 'id_sap', 'sap_customer']
    
    def filter_queryset(self, queryset, *args, **kwargs):
        if 'sap_customer' not in self.data:
            return queryset

        return queryset.filter(
            user__accessapplication__details__sap_customer=self.data.get('sap_customer'))