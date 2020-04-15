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

    link = "http://{}/#/user/{}/{}/reset-password/".format(
        access.application.domain,
        urlsafe_base64_encode(force_bytes(user.pk)),
        default_token_generator.make_token(user)
    )
    context = {'user': user, 'link': link}
    template_name = 'emails/acces_pcis_portal.html'
    email_template = get_template(template_name)

    html_message = email_template.render(context)

    return send_mail(
        'Subject',
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message)


def create_father(row):
    merchant, _ = Merchant.objects.get_or_create(
        name=MERCHANT_NAME, number=MERCHANT_NUMBER)

    application_pci, create = Application.objects.get_or_create(
        name='Portal PCIS', merchant=merchant)

    user, create = UserModel.objects.get_or_create(
        username=row.get('email'),
        email=row.get('email')
    )

    if create:
        user.first_name = row.get('name')
        user.save()

        resident, _ = Resident.objects.get_or_create(
            name=row.get('name'),
            email=row.get('email'),
            identification='-', telephone='',
            id_sap=row.get('id_sap'),
            sap_customer=row.get('sap_customer'),
            user=user
        )

    access, create_access = AccessApplication.objects.get_or_create(
        user=user, application=application_pci,
    )

    if create_access:
        access.details.create(sap_customer=row.get('sap_customer'))
    
    send_access_email.delay(user.id, application_pci.id, create)
    return user


def run():
    root_project = lambda *x: os.path.join(settings.ROOT_PROJECT, *x) # noqa
    with open(root_project('father_pci.csv')) as f:
        reader = f.readlines()
    map(create_father, reader)
