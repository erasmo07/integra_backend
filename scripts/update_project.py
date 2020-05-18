# -*- coding: utf-8 -*-
import csv
import json
import os

from django.conf import settings
from django.db.utils import IntegrityError
from integrabackend.resident.models import Property, Project


def assign_project(row):
    property_ = Property.objects.filter(
        id=row.get('UUID_PROPIEDAD'), project__isnull=False)

    if property_.exists():
        project = Project.objects.get(id=row.get('UUID_PROYECTO'))
        property_.first().project = project
        property_.first().save()

def run():
    root_project = lambda *x: os.path.join(settings.ROOT_PROJECT, *x) # noqa
    reader = csv.DictReader(open(root_project('property_x_project.csv')))
    for row in reader:
        assign_project(row)