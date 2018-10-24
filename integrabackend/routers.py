from rest_framework.routers import DefaultRouter
from .users.views import UserViewSet
from .resident.views import (
    ResidentCreateViewSet, PersonViewSet, PropertyViewSet)
from .invitation.views import InvitationViewSet, TypeInvitationViewSet
from .solicitude.views import (
    ServiceViewSet, StateSolicitudeServiceViewSet,
    ServiceRequestViewSet, DayViewSet)


router = DefaultRouter()

# APP - User
router.register(r'users', UserViewSet)

# APP - Resident
router.register(r'resident', ResidentCreateViewSet)
router.register(r'propery', PropertyViewSet)

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
router.register(r'day', DayViewSet)