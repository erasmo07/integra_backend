from django.forms.models import model_to_dict
from django.urls import reverse
from faker import Faker
from nose.tools import eq_, ok_
from rest_framework import status
from rest_framework.test import APITestCase

from ...users.test.factories import UserFactory
from . import factories

fake = Faker()


class TestPaymenetAttemptTestCase(APITestCase):

    def setUp(self):
        self.url = '/api/v1/payment-attempt/'
        self.keys_expect = [
            'sap_customer', 'date', 'id', 'invoices',
            'process_payment', 'transaction', 'user',
        ]
        self.keys_expect_invoices = [
            'id', 'amount', 'amount_dop', 'company',
            'company_name', 'day_pass_due', 'description',
            'document_date', 'document_number', 'tax',
            'is_expired', 'merchant_number', 'currency',
            'position', 'reference',
        ]
    
    def test_can_list_payments_without_documents(self):
        # GIVEN
        payment_attempt = factories.PaymentAttemptFactory()

        # WHEN
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.url)

        # THEN
        for payment_attempt in response.json():
            for key in self.keys_expect:
                self.assertIn(key, payment_attempt)
    
    def test_can_create_payments_attempt(self):
        # GIVE
        payment_attempt = factories.PaymentAttemptFactory()
        invoice_data = model_to_dict(factories.InvoiceFactory())
        invoice_data.pop('payment_attempt')


        data = model_to_dict(payment_attempt)
        data['invoices'] = [invoice_data]

        # WHEN
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        response = self.client.post(self.url, data, format='json')

        #THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in self.keys_expect:
            self.assertIn(key, response.json())

        for invoice in response.json().get('invoices'):
            for key in self.keys_expect_invoices:
                self.assertIn(key, invoice)

