import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from integrabackend.invitation import models


class InvitationFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='query_filter')
    date_entry = django_filters.DateFilter(field_name='date_entry')

    class Meta:
        model = models.Invitation
        fields = [
            'search',
            'number',
            'status',
            'date_entry',
            'ownership__address',
            'invitated__name']
    
    def query_filter(self, queryset, name, value):
        """
        Solution find in 
            https://stackoverflow.com/questions/57270470/
            django-filter-how-to-make-multiple-fields-search-with-django-filter
        """
        return self.Meta.model.objects.filter(
            Q(invitated__name__icontains=value) |
            Q(ownership__address__icontains=value) |
            Q(number__icontains=value))