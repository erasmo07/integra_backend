import base64
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.conf import settings
from partenon.helpdesk import HelpDeskUser, Topics, Prioritys, Status, HelpDeskTicket
from partenon.ERP import ERPAviso
from . import enums, models


class ServiceRequestHasAviso(Exception):
    pass


def create_service_request(instance):
    """ Function Docstring """
    helpdesk_user = HelpDeskUser.create_user(
        instance.user.email, instance.user.first_name,
        instance.user.last_name)
    topic = Topics.objects.get_by_name(instance.service.name)
    priority = Prioritys.objects.get_by_name('Normal')
    ticket = helpdesk_user.ticket.create(
        'Subject', instance.note, priority, topic)
    instance.ticket_id = ticket.ticket_id
    instance.save()


def process_to_create_aviso(
    service_request,
    model_state=models.State,
    state_names=enums.StateEnums.service_request):
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
        state, _ = model_state.objects.get_or_create(
            name=state_names.notice_created)
        service_request.aviso_id = aviso.aviso
        service_request.state = state
        service_request.save()


def upload_quotation(
    service_request,
    aviso_class=ERPAviso):

    # CREATE COTATTION
    erp_aviso = aviso_class(**dict(aviso=service_request.aviso_id))
    blob = erp_aviso.create_quotation()
    quotation_file_name = '%s.pdf' % service_request.aviso_id
    quotation_file = ContentFile(
        base64.b64decode(blob),
        name=quotation_file_name)
    service_request.quotation.file = quotation_file
    service_request.quotation.save()


def make_quotation(
    service_request,
    model=models.Quotation,
    model_state=models.State,
    states=enums.StateEnums):
    state_pending, _ = model_state.objects.get_or_create(
        name=states.quotation.pending)
    quotation_data = dict(
        service_request=service_request, state=state_pending)
    quotation, _ = model.objects.get_or_create(**quotation_data)
    upload_quotation(service_request)


def notify_valid_quotation(
    service_request,
    subjects=enums.Subjects,
    email_class=EmailMessage):
    # SEND EMAIL TO CLIENT
    subject = subjects.build_subject( 
        subjects.valid_quotation,
        service_request.ticket_id)
    message = 'Here is the message for valid work'
    recipient_list = [service_request.email]
    email = email_class(
        subject=subject, body=message,
        to=recipient_list, cc=[settings.DEFAULT_SOPORT_EMAIL])
    email.attach(
        service_request.quotation.file.name,
        service_request.quotation.file.read(),
        'application/pdf')
    email.send()


def notify_valid_work(
    service_request,
    subjects=enums.Subjects,
    email_class=EmailMessage):
    # SEND EMAIL TO CLIENT
    subject = subjects.build_subject( 
        subjects.valid_work,
        service_request.ticket_id)
    message = 'Here is the message for valid work'
    recipient_list = [service_request.email]
    email = email_class(
        subject=subject, body=message,
        to=recipient_list, cc=[settings.DEFAULT_SOPORT_EMAIL])
    email.send()


def client_valid_quotation(
    service_request,
    model_state=models.State,
    states=enums.StateEnums,
    ticket_class=HelpDeskTicket,
    ticket_state=Status):
    """
    Function to notify the client for aprove or reject
    cotization of service.
    """
    make_quotation(service_request)

    # UPDATE TICKET STATE WAITING APPROVAL
    ticket = ticket_class(ticket_id=service_request.ticket_id)
    ticket_state_name = states.ticket.waiting_approval
    status_ticket = ticket_state.get_state_by_name(ticket_state_name)
    ticket.change_state(status_ticket)

    # UPDATE SERVICE REQUES STATE APROVE QUOTATION
    state, _ = model_state.objects.get_or_create(
        name=states.service_request.waith_valid_quotation)
    service_request.state = state
    service_request.save()

    notify_valid_quotation(service_request)


def client_valid_work(
    service_request,
    states=enums.StateEnums,
    model_state=models.State,
    subjects=enums.Subjects):
    """
    Function to notify the client for aprove or reject
    work realized.
    """
    # UPDATE SERVICE REQUES STATE APROVE WORK 
    state, _ = model_state.objects.get_or_create(
        name=states.service_request.waith_valid_work)
    service_request.state = state
    service_request.save()

    # UPDATE TICKET STATE WAITING APPROVAL
    ticket = HelpDeskTicket(ticket_id=service_request.ticket_id)
    status_ticket = Status.get_state_by_name(states.ticket.waith_valid_work)
    ticket.change_state(status_ticket)
    
    notify_valid_work(service_request) 


def aprove_quotation(
    service_request,
    model_state=models.State,
    states=enums.StateEnums):
    """ Process for aprove quotation """

    # UPDATE TICKE ON HELPDESK
    status = Status.get_state_by_name(states.ticket.aprove_quotation)
    ticket = HelpDeskTicket(ticket_id=service_request.ticket_id)
    ticket.change_state(status)

    # UPDATA AVISO ON EPR SYSTEM
    ERPAviso.update(
        service_request.aviso_id,
        states.aviso.aprove_quotation)
    
    # UPDATE QUOTATION REGISTER
    state_aprove, _ = model_state.objects.get_or_create(
        name=states.quotation.approved)
    service_request.quotation.state = state_aprove
    service_request.quotation.save()

    # UPDATE SERVICE REQUEST STATE
    state_service_request, _ = model_state.objects.get_or_create(
        name=states.service_request.approve_quotation)
    service_request.state = state_service_request
    service_request.save()


def approve_work(
    service_request,
    states=enums.StateEnums,
    model_state=models.State):
    """ Process for aprove work """

    # UPDATE SERVICE REQUEST STATE TO APPROVED
    state, _ = model_state.objects.get_or_create(
        name=states.service_request.approved)
    service_request.state = state
    service_request.save()

    # CLOSE TICKET
    ticket = HelpDeskTicket(ticket_id=service_request.ticket_id)
    ticket.close()

    # UPDATE AVISO STATE ON EPR SYSTEM
    ERPAviso.update(
        service_request.aviso_id,
        states.aviso.accepted_work)


def reject_quotation(
    service_request,
    model_state=models.State,
    states=enums.StateEnums):
    """ Process for reject quotation """
    # CLOSE TICKET
    ticket = HelpDeskTicket(ticket_id=service_request.ticket_id)
    ticket.close()

    # UPDATE AVISO TO REJECT STATE
    ERPAviso.update(
        service_request.aviso_id,
        enums.AvisoEnums.reject_quotation)

    # UPDATE QUOTATION REGISTER
    state_reject, _ = model_state.objects.get_or_create(
        name=states.quotation.reject)
    service_request.quotation.state = state_reject
    service_request.quotation.save()