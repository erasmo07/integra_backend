from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (AccessApplication, AccessDetail, Application, Merchant,
                     User)
from .permissions import (IsApplicationUserPermission,
                          IsBackOfficeUserPermission, IsUserOrReadOnly)
from .serializers import (AccessApplicationSerializer, ApplicationSerializer,
                          MerchantSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """
    Updates and retrieves user accounts
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('username', 'email')


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    View all application register
    """
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsApplicationUserPermission]


class AccessApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View all access-application register
    """
    queryset = AccessApplication.objects.all()
    serializer_class = AccessApplicationSerializer 
    permission_classes = [IsApplicationUserPermission]

    filter_backends = (DjangoFilterBackend,)
    filter_fields = '__all__'

    @action(detail=True, methods=['PUT'], url_path='remove-detail')
    def remove_details(self, request, pk):
        access_application = self.get_object()

        access_detail = get_object_or_404(
            AccessDetail, pk=request.data.get('id'))
        access_application.details.remove(access_detail)
        return Response({})


class MerchantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer
    permission_classes = [IsBackOfficeUserPermission]

    filter_backends = (DjangoFilterBackend,)
    filter_fields = '__all__'
