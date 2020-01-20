import random

from django.test import TestCase
from integrabackend.resident.test.factories import ResidentFactory
from . import factories
from .. import helpers


class TestCompensationPayment(TestCase):

    def setUp(self):
        user = factories.UserFactory()
        resident = ResidentFactory(user=user)
        self.transaction_payment = factories.PaymentAttemptFactory(user=user)

        factories.ResponsePaymentAttempt(payment_attempt=self.transaction_payment) 

        for _ in range(random.randint(1, 10)):
            factories.InvoiceFactory(
                payment_attempt=self.transaction_payment)
        
        for _ in range(random.randint(1, 5)):
            factories.AdvancePaymentFactory(
                payment_attempt=self.transaction_payment)

    def test_compensation_payment_send_corect_keys(self):
        # WHEN
        compensation_payment = helpers.CompensationPayment(self.transaction_payment)
        data = compensation_payment.build_request_body()

        # THEN
        keys = [
            'customer', 'language', 'datos_tranf',
            'invoice', 'advancepayment']

        keys_invoice = [
            'amount_dop', 'company', 'company_name', 'currency',
            'description', 'document_number', 'merchant_number',
            'position', 'reference', 'tax']

        keys_advance = [
            'bukrs', 'description', 'amount',
            'currency', 'position', 'merchant_number']

        for key in keys:
            self.assertIn(key, data)
        
        for invoice in data.get('invoice'):
            for key in keys_invoice:
                self.assertIn(key, invoice)
        
        for advance in data.get('advancepayment'):
            for key in keys_advance:
                self.assertIn(key, advance)