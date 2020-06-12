from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import get_template
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from integrabackend.celery import app
from integrabackend.resident.models import Resident

UserModel = get_user_model()
logger = get_task_logger(__name__)


@app.task
def send_access_email(user_id, application_id, new_user):
    user = UserModel.objects.get(id=user_id)

    access = user.accessapplication_set.filter(
        application__id=application_id
    ).first()

    template='acces_pcis_portal_new_user' if new_user else 'acces_pcis_portal'
    template_name='emails/%s.html' % template

    email_template = get_template(template_name)

    link = "{}/#/user/{}/{}/reset-password/".format(
        access.application.domain,
        urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        default_token_generator.make_token(user),
    )

    link_portal = 'http://{}/'.format(access.application.domain)

    context={
        'user': user, 'link': link,
        'link_portal': link_portal,
        'application_name': access.application.name}
    html_message=email_template.render(context)

    send_mail(
        f'Acceso a portal de pagos de {access.application.name}',
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message)
