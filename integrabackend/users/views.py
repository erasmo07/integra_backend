from rest_framework import viewsets, mixins, generics
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Application
from .permissions import IsUserOrReadOnly, IsApplicationUserPermission
from .serializers import UserSerializer, ApplicationSerializer


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
