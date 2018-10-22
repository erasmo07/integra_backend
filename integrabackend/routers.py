from rest_framework.routers import DefaultRouter
from .users.views import UserViewSet
from .resident.views import ResidentCreateViewSet, PersonViewSet
from .invitation.views import InvitationViewSet, TypeInvitationViewSet
from .solicitude.views import (
    ServiceViewSet, StateSolicitudeServiceViewSet,
    ServiceRequestViewSet)


router = DefaultRouter()
# APP - User
router.register(r'users', UserViewSet)

# APP - Resident
router.register(r'resident', ResidentCreateViewSet)

# APP - Invitation
router.register(
    r'type-invitation',
    TypeInvitationViewSet,
    base_name='type-invitation')
router.register(r'invitation', InvitationViewSet)
router.register(r'person', PersonViewSet)

# APP - solicitude
router.register(r'service', ServiceViewSet)
router.register(r'state/solicitude', StateSolicitudeServiceViewSet)
router.register(r'service-request', ServiceRequestViewSet)