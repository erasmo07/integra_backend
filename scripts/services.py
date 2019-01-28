# -*- coding: utf-8 -*-
import csv
import os
from django.conf import settings
from integrabackend.solicitude.models import Service


def run():
    root_project = lambda *x: os.path.join(settings.ROOT_PROJECT, *x) # noqa
    reader = csv.DictReader(open(root_project('services.csv'), encoding="ISO-8859-1"))

    for row in reader:
        name = u"{}".format(row.get('service_name')).encode('utf-8').strip()
        obj, create = Service.objects.get_or_create(
            name=name, sap_code_service="S4")