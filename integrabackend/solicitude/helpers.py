from partenon.helpdesk import HelpDeskUser, Topics, Prioritys


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