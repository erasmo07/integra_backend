from django.db.utils import IntegrityError
from integrabackend.users.models import (
    User, AccessApplication, Application, Merchant,
    AccessDetail)

MERCHANT_NAME = 'PORTAL CLIENTES'
MERCHANT_NUMBER = '9999'

def run():
    merchant, _ = Merchant.objects.get_or_create(
        name=MERCHANT_NAME, number=MERCHANT_NUMBER)

    application, _ = Application.objects.get_or_create(
        name=MERCHANT_NAME, merchant=merchant)

    users = User.objects.filter(password__isnull=False)

    for user in users:
        AccessApplication.objects.get_or_create(
            user=user, application=application,
        )