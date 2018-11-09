from partenon.helpdesk import HelpDeskUser, Topics, Prioritys
from partenon.ERP import ERPAviso


class ServiceRequestHasAviso(Exception):
    pass


def process_to_create_service_request(instance):
    helpdesk_user = HelpDeskUser.create_user(
        instance.user.email,
        instance.user.first_name,
        instance.user.last_name)
    topic = Topics.objects.get_by_name(instance.service.name) 
    priority = Prioritys.objects.get_by_name('Normal')
    ticket = helpdesk_user.ticket.create(
        'Subject', instance.note, priority, topic)
    instance.ticket_id = ticket.ticket_id
    instance.save()


def process_to_create_aviso(service_request):
    if service_request.aviso_id:
        raise ServiceRequestHasAviso(
            'Esta solicitud ya tiene un aviso')
    
    erp_aviso = ERPAviso()
    aviso = erp_aviso.create(
        service_request.sap_customer,
        "TITULO", "NOTA",
        service_request.service.name,
        service_request.email,
        service_request.service.sap_code_service)
    if hasattr(aviso, 'aviso'):
        service_request.aviso_id = aviso.aviso
        service_request.save()