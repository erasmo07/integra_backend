# -*- coding: utf-8 -*-
import csv
import json
import os

import requests
from celery.decorators import task
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
from integrabackend.users.models import (AccessApplication, Application,
                                         Merchant)

UserModel = get_user_model()

MERCHANT_NAME = 'PCIS'
MERCHANT_NUMBER = '0000'


@task
def send_access_email(user_id, application_id, new_user):
    user = UserModel.objects.get(id=user_id)

    access = user.accessapplication_set.filter(
        application__id=application_id
    ).first()

    template = 'acces_pcis_portal_new_user' if new_user else 'acces_pcis_portal'
    template_name = 'emails/%s.html' % template

    email_template = get_template(template_name)

    params = '?utm_source=email&utm_medium='\
             'email&utm_campaign=launch_pcis_portal'

    link = "http://{}/#/user/{}/{}/reset-password/{}".format(
        access.application.domain,
        urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        default_token_generator.make_token(user),
        params
    )

    link_portal = 'http://{}/{}'.format(access.application.domain, params)

    context = {
        'user': user, 'link': link,
        'link_portal': link_portal}
    html_message = email_template.render(context)

    return send_mail(
        'Acceso a portal de pagos del Puntacana International School - PCIS',
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message)


def create_father(row):
    merchant, _ = Merchant.objects.get_or_create(
        name=MERCHANT_NAME, number=MERCHANT_NUMBER)

    application_pci, create = Application.objects.get_or_create(
        name='Portal PCIS', merchant=merchant)

    user = UserModel.objects.filter(username=row.get('email'))
    
    if user.exists():
        user = user.first()
        user_created = False
    else:
        user = UserModel.objects.create(
            username=row.get('email'),
            email=row.get('email')
        )
        user_created = True

    resident = Resident.objects.filter(
        sap_customer=row.get('sap_customer'))
    
    if resident.exists() and not hasattr(user, 'resident'):
        resident.update(user=user)

    user.refresh_from_db()

    if not hasattr(user, 'resident'):
        Resident.objects.get_or_create(
            name=row.get('name'),
            email=row.get('email'),
            identification='-',
            telephone='',
            id_sap=row.get('id_sap'),
            sap_customer=row.get('sap_customer'),
            user=user)
    

    access, create_access = AccessApplication.objects.get_or_create(
        user=user, application=application_pci,
    )

    send_access_email(user.id, application_pci.id, user_created)
    return user


def run():
    root_project = lambda *x: os.path.join(settings.ROOT_PROJECT, *x) # noqa
    reader = csv.DictReader(open(root_project('father_pcis.csv')))
    for row in reader:
        create_father(row)