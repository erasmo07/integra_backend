from rest_framework.routers import DefaultRouter

from .invitation import views as invitation_views
from .payment import views as payment_views
from .proxys import views as proxys
from .resident.views import (AreaViewSet, DepartmentViewSet,
                             OrganizationViewSet, PersonViewSet,
                             ProjectViewSet, PropertyTypeViewSet,
                             PropertyViewSet, ResidentCreateViewSet,
                             TypeIdentificationViewSet)
from .solicitude.views import (AvisoViewSet, DayViewSet, ServiceRequestViewSet,
                               ServiceViewSet, StateSolicitudeServiceViewSet)
from .users.views import (AccessApplicationViewSet, ApplicationViewSet,
                          MerchantViewSet, UserViewSet)
from .webhook import views as webhooks

router = DefaultRouter()

# APP - User
router.register(r'users', UserViewSet)
router.register(r'application', ApplicationViewSet)
router.register(r'access-application', AccessApplicationViewSet)
router.register(r'merchant', MerchantViewSet)

# APP - Resident
router.register(r'area', AreaViewSet)
router.register(r'department', DepartmentViewSet)
router.register(r'resident', ResidentCreateViewSet)
router.register(r'property', PropertyViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'property-type', PropertyTypeViewSet)
router.register(r'type-identification', TypeIdentificationViewSet)
router.register(r'organization', OrganizationViewSet)

# APP - Invitation
router.register(r'type-invitation', invitation_views.TypeInvitationViewSet)
router.register(r'status-invitation', invitation_views.StatusInvitationViewSet)
router.register(r'medio', invitation_views.MedioViewSet)
router.register(r'color', invitation_views.ColorViewSet)
router.register(r'invitation', invitation_views.InvitationViewSet)
router.register(r'person', PersonViewSet)

# APP - solicitude
router.register(r'service', ServiceViewSet)
router.register(
    r'state/solicitude', StateSolicitudeServiceViewSet)
router.register(r'service-request', ServiceRequestViewSet)
router.register(r'day', DayViewSet)
router.register(
    r'aviso', AvisoViewSet, base_name='create_aviso')


# APP - Payment
router.register(
    r'state-process-payment',
    payment_views.StateProcessPaymentViewSet)
router.register(
    r'state-compensation',
    payment_views.StateCompensationViewSet)

router.register(
    r'verifone',
    payment_views.VerifoneViewSet
)

router.register(
    r'payment-attempt',
    payment_views.PaymentAttemptViewSet,
    base_name='payment_attempt')

router.register(
    r'credit-card',
    payment_views.CreditCardViewSet,
    base_name='credit_card')

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
    r'sap/client',
    proxys.ERPClientViewSet,
    base_name='client')


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

router.register(
    r'sap/temporal-invoice',
    proxys.TemporalInvoiceViewSet,
    base_name='temporal_invoice'
)

# WEBHOOK
router.register(
    r'faveo-webhook',
    webhooks.FaveoWebHookView,
    base_name="faveo_webhook")
