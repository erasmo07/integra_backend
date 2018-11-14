from django.core.mail import send_mail
from django.conf import settings
from partenon.helpdesk import HelpDeskUser, Topics, Prioritys
from partenon.ERP import ERPAviso
from . import enums 


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
    """
    Function to create a new aviso on service-request
    """
    if service_request.aviso_id:
        raise ServiceRequestHasAviso(
            'Esta solicitud ya tiene un aviso')
    
    erp_aviso = ERPAviso()
    aviso = erp_aviso.create(
        service_request.sap_customer,
        "TITULO", "NOTA",
        service_request.service.name,
        service_request.email,
        service_request.service.sap_code_service,
        require_quotation=service_request.require_quotation)
    if hasattr(aviso, 'aviso'):
        service_request.aviso_id = aviso.aviso
        service_request.save()


def notify_to_aprove_or_reject_service(service_request):
    """
    Function to notify the client for aprove or reject
    cotization of service.
    """
    send_mail(
        subject=enums.Subjects.aprove_or_reject_service,
        message='Here is the message',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[service_request.email])