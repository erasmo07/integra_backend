from rest_framework.routers import DefaultRouter
from .users.views import UserViewSet
from .resident.views import ResidentCreateViewSet, PersonViewSet
from .invitation.views import InvitationViewSet, TypeInvitationViewSet
from .solicitude.views import ServiceViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'resident', ResidentCreateViewSet)
router.register(r'invitation', InvitationViewSet)
router.register(
    r'type-invitation',
    TypeInvitationViewSet,
    base_name='type-invitation')
router.register(r'person', PersonViewSet)
router.register(r'service', ServiceViewSet)