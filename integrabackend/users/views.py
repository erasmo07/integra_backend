from rest_framework import viewsets, mixins, generics
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Application, Merchant, AccessApplication
from .permissions import (
    IsUserOrReadOnly, IsBackOfficeUserPermission,
    IsApplicationUserPermission)
from .serializers import (
    UserSerializer,
    ApplicationSerializer,
    AccessApplicationSerializer,
    MerchantSerializer)


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


class MerchantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer
    permission_classes = [IsBackOfficeUserPermission]

    filter_backends = (DjangoFilterBackend,)
    filter_fields = '__all__'