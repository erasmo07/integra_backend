from django.core.mail import send_mail
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


def client_valid_quotation(
    service_request,
    model_state=models.State,
    model_quotation=models.Quotation,
    states=enums.StateEnums,
    ticket_class=HelpDeskTicket,
    subject=enums.Subjects.valid_quotation):
    """
    Function to notify the client for aprove or reject
    cotization of service.
    """
    # SEND EMAIL TO CLIENT
    send_mail(
        subject=subject,
        message='Here is the message valid quotation',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[service_request.email])

    # UPDATE TICKET STATE WAITING APPROVAL
    ticket = ticket_class(ticket_id=service_request.ticket_id)
    status_ticket = Status.get_state_by_name(states.ticket.waiting_approval)
    ticket.change_state(status_ticket)

    # MAKE QUOTATION REGISTER
    state_pending, _ = model_state.objects.get_or_create(
        name=states.quotation.pending)
    quotation_data = dict(
        service_request=service_request, state=state_pending)
    quotation, _ = model_quotation.objects.get_or_create(**quotation_data)

    # UPDATE SERVICE REQUES STATE APROVE QUOTATION
    state, _ = model_state.objects.get_or_create(
        name=states.service_request.waith_valid_quotation)
    service_request.state = state
    service_request.save()


def client_valid_work(
    service_request,
    states=enums.StateEnums,
    subject=enums.Subjects.valid_work,
    model_state=models.State):
    """
    Function to notify the client for aprove or reject
    work realized.
    """
    # SEND EMAIL TO CLIENT
    send_mail(
        subject=subject,
        message='Here is the message for valid work',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[service_request.email])
    
    # UPDATE SERVICE REQUES STATE APROVE WORK 
    state, _ = model_state.objects.get_or_create(
        name=states.service_request.waith_valid_work)
    service_request.state = state
    service_request.save()

    # UPDATE TICKET STATE WAITING APPROVAL
    ticket = HelpDeskTicket(ticket_id=service_request.ticket_id)
    status_ticket = Status.get_state_by_name(states.ticket.waith_valid_work)
    ticket.change_state(status_ticket)


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
    """
    ERPAviso.update(
        service_request.aviso_id,
        states.aviso.aprove_quotation)
    """
    
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


def reject_quotation(service_request):
    """ Process for reject quotation """

    # UPDATE AVISO TO REJECT STATE
    ERPAviso.update(
        service_request.aviso_id,
        enums.AvisoEnums.reject_quotation)
