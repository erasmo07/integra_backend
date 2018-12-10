from django.db.models import Q


class StateSolicitudeServiceEnums:
    draft = 'Abierto'
    notify_cotization = 'Espera de aprobación'
    notice_created = 'Abierto' 
    waith_valid_work = 'Pendiente de aprobación de trabajo'
    waith_valid_quotation = "Pendiente aprobación cotizacion"
    approve_quotation = 'Cotización aprobada'
    reject_quotation = 'Cotizacion rechazada'
    reject_work = "Trabajo Rechazado"
    approved = 'Cerrado'

    @property
    def limit_choice(self):
        return Q(name=self.draft)


class AvisoEnums:
    aprove_quotation = 'coap'
    reject_quotation = 'core'
    requires_quote_approval = 'raco'
    requires_acceptance_closing = 'race'
    accepted_work = 'acep'


class TicketStatusenums:
    aprove_quotation = 'Cotiz aprobada cli'
    reject_work = 'Trabajo rechaz cli'
    waiting_approval_quotation = 'Pend aprobar cotiz'
    waiting_validate_work = 'Pend aprobar trab'


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

    @staticmethod
    def build_subject(text, ticket_id):
        return "{0} [#N{1}]".format(text, ticket_id)


class Message:

    def build_reject_work(service_request, aviso):
        message = f'Apreciado {aviso.responsable.nombre} \n\n'\
            f'El cliente {service_request.user.get_full_name()} '\
            f'rechazo el trabajo de {service_request.service.name} '\
            f'relacionado con el aviso '\
            f'{service_request.aviso_id} \n\n'\
            f'Por favor comuníquese  con el cliente para validar las '\
            f'razones del rechazo al {aviso.client.telefono}\n\n'\
            f'Categoría de cliente: {aviso.client.clasification_name}.\n\n'\
            f'Ubicación Técnica: {service_request.property.direction}.\n\n'\
            f'Gracias'
        return message