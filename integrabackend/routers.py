from rest_framework.routers import DefaultRouter
from .users.views import UserViewSet
from .resident.views import (
    ResidentCreateViewSet, PersonViewSet, PropertyViewSet, PropertyTypeViewSet)
from .invitation.views import InvitationViewSet, TypeInvitationViewSet
from .solicitude.views import (
    ServiceViewSet, StateSolicitudeServiceViewSet,
    ServiceRequestViewSet, DayViewSet, AvisoViewSet)
from .proxys import views as proxys
from .webhook import views as webhooks


router = DefaultRouter()

# APP - User
router.register(r'users', UserViewSet)

# APP - Resident
router.register(r'resident', ResidentCreateViewSet)
router.register(r'property', PropertyViewSet)
router.register(r'property-type', PropertyTypeViewSet)

# APP - Invitation
router.register(
    r'type-invitation',
    TypeInvitationViewSet,
    base_name='type-invitation')
router.register(r'invitation', InvitationViewSet)
router.register(r'person', PersonViewSet)

# APP - solicitude
router.register(r'service', ServiceViewSet)
router.register(
    r'state/solicitude', StateSolicitudeServiceViewSet)
router.register(r'service-request', ServiceRequestViewSet)
router.register(r'day', DayViewSet)
router.register(
    r'aviso', AvisoViewSet, base_name='create_aviso')

# PROXYS
router.register(
    r'search-client',
    proxys.SearchClientViewSet,
    base_name='search_client')

router.register(
    r'client-info',
    proxys.ClientInfoViewSet,
    base_name='client_info')

router.register(
    r'client-has-credit',
    proxys.ClientHasCreditViewSet,
    base_name='client_has_credit')

router.register(
    r'client-emails',
    proxys.ClientAddEmailViewSet,
    base_name='client-email')

router.register(
    r'sap/resident',
    proxys.ERPResidentsViewSet,
    base_name='residents')

router.register(
    r'faveo/ticket',
    proxys.FaveoTicketDetailViewSet,
    base_name='faveo_ticket')

router.register(
    r'sap/resident/principal-email',
    proxys.ERPResidentsPrincipalEmailViewSet,
    base_name='principal_emails')

router.register(
    r'sita-db/departure-flight',
    proxys.SitaDBDepartureFlightViewSet,
    base_name='sita_departure_flight'
)

router.register(
    r'sita/get-flight',
    proxys.SitaFlightViewSet,
    base_name='get_flight'
)

# WEBHOOK
router.register(
    r'faveo-webhook',
    webhooks.FaveoWebHookView,
    base_name="faveo_webhook")
