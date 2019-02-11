# -*- coding: utf-8 -*-
import csv
import os
import requests
import json
from django.conf import settings


def run():
    root_project = lambda *x: os.path.join(settings.ROOT_PROJECT, *x) # noqa
    import ipdb; ipdb.set_trace()
    with open(root_project('services.txt')) as f:
        reader = f.readlines()

    for service_name in reader:
        token = '2192d6b7b33361356ba0d5c6a8141a85ac771cc7'
        header = {
            "Authorization": 'Token {}'.format(token),
            "Content-Type": "application/json"}

        service_data = {"name": service_name, 'sap_code_service': 'S4'}
        service = requests.post(
            "http://87.4.5.140/api/v1/service/", 
            data=json.dumps(service_data), 
            headers=header)

