from django.db.models import Q


class StateSolicitudeServiceEnums:
    draft = 'x'
    notify_cotization = 'Espera de aprobacion'
    notice_created = 'Aviso Creado' 
    waith_valid_work = 'Pendiente de aprovabacion de trabajo'
    waith_valid_quotation = "Pendiente de aprobacion de cotización"
    approve_quotation = 'Cotización aprovada'
    reject_quotation = 'Cotizacion rechazada'
    approved = 'Solicitud aprobada'

    @property
    def limit_choice(self):
        return Q(name=self.draft)


class AvisoEnums:
    aprove_quotation = 'COAP'
    reject_quotation = 'CORE'
    requires_quote_approval = 'RACO'
    requires_acceptance_closing = 'RACE'
    accepted_work = 'ACEP'


class TicketStatusenums:
    aprove_quotation = 'Revisado'
    waiting_approval = 'On Hold'
    waith_valid_work = 'Resolved'


class QuotationEnums:
    pending = 'Pendinte'
    approved = 'Aprovada'
    reject = 'Rechazada'


class StateEnums:
    service_request = StateSolicitudeServiceEnums()
    aviso = AvisoEnums()
    ticket = TicketStatusenums()
    quotation = QuotationEnums()


class Subjects:
    valid_quotation = "Aprovar o Rechazar cotizacion"
    valid_work = "Validar Trabajo realizado"
