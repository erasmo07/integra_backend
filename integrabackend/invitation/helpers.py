import barcode
from barcode.writer import ImageWriter
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.core.files import File
from django.template.loader import get_template

from integrabackend.celery import app
from integrabackend.invitation.enums import Subjects
from integrabackend.invitation.models import Invitation

logger = get_task_logger(__name__)

@app.task(name="notify_invitation")
def notify_invitation(
        invitation_id,
        email_template='emails/invitation/notify.html',
        email_class=EmailMessage):
    invitation = Invitation.objects.get(id=invitation_id)

    if invitation.is_supplier:
        return

    if not invitation.barcode:
        barcode.get(
            'ean13',
            f'{invitation.number}',
            writer=ImageWriter()
        ).save(f'invitation_{invitation.number}')

        with open(f'invitation_{invitation.number}.png', 'rb') as f:
            invitation.barcode.save(
                f'invitation_{invitation.number}.png',
                File(f), save=True)

    email_template = get_template(email_template)

    invitation_property = [
        ('Propiedad a vistiar', invitation.ownership.address),
        ('Nombre del invitado (titular)', invitation.invitated.name),
        ('Número de acompañantes', 3),
        ('Identificación', invitation.invitated.identification),
        ('Fecha de inicio de la visita',
         invitation.date_entry.strftime('%d-%m-%Y')),
        ('Fecha en que termina la visita',
         invitation.date_out.strftime('%d-%m-%Y')),
        ('Comentario de quien realiza la invitación', invitation.note)
    ]
    context = {
        'invitation_property': invitation_property,
        'invitation_number': invitation.number,
        'invitation_barcode_src': invitation.barcode.url,
    }

    msg = email_class(
        Subjects.send_notification,
        email_template.render(context),
        settings.DEFAULT_FROM_EMAIL,
        to=[invitation.invitated.email], cc=[invitation.create_by.email])
    msg.content_subtype = "html"  # Main content is now text/html
    msg.send()

    return True
