from mock import patch, MagicMock

from django.forms.models import model_to_dict
from django.urls import reverse
from faker import Faker
from nose.tools import eq_, ok_
from rest_framework import status
from rest_framework.test import APITestCase

from oraculo.gods.exceptions import BadRequest
from partenon.process_payment import azul

from ...users.test.factories import UserFactory, GroupFactory
from integrabackend.resident.test.factories import ResidentFactory
from . import factories
from .. import models

fake = Faker()


class TestCreditCardTestCase(APITestCase):

    def setUp(self):
        self.keys_expects = ['id', 'brand', 'name']

        self.user = UserFactory()
        factories.CreditCardFactory(
            brand='VISA',
            name='Name',
            data_vault_expiration='202011',
            owner=self.user,
            token='5EB29277-E93F-4D1F-867D-8E54AF97B86F')
        self.client.force_authenticate(user=self.user)

    def test_can_list_credit_card(self):
        credit_card = self.client.get('/api/v1/credit-card/')

        self.assertEqual(credit_card.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(credit_card.json()))

        for credit_card in credit_card.json():
            for key in self.keys_expects:
                self.assertIn(key, credit_card)

    def test_can_register_two_credit_card(self):
        factories.CreditCardFactory(
            brand='VISA', name='Name',
            data_vault_expiration='202011',
            owner=self.user,
            token='5EB29277-E93F-4D1F-867D-8E54AF97B86F')

        credit_card = self.client.get('/api/v1/credit-card/')

        self.assertEqual(credit_card.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(credit_card.json()))

        for credit_card in credit_card.json():
            for key in self.keys_expects:
                self.assertIn(key, credit_card)
    
    def test_can_filter_by_owner(self):
        user = UserFactory()
        user.groups.add(GroupFactory(name='Aplicacion'))
        
        factories.CreditCardFactory(
            brand='VISA',
            name='Name',
            data_vault_expiration='202011',
            owner=self.user,
            token='5EB29277-E93F-4D1F-867D-8E54AF97B86F')

        params = dict(owner=self.user)
        response = self.client.get('/api/v1/credit-card/', params=params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), self.user.credit_card.count())
    
    def test_can_delete_credit_card(self):
        user = UserFactory()
        user.groups.add(GroupFactory(name='Aplicacion'))

        token, token_expiration, brand = azul.Card(
            number='4035874000424977',
            expiration='202012',
            cvc='977'
        ).validate(amount='100', code='CODE')
        
        credit_card = factories.CreditCardFactory(
            brand=brand,
            name='Name',
            data_vault_expiration=token_expiration,
            owner=self.user,
            token=token
        )

        response = self.client.delete('/api/v1/credit-card/%s/' % credit_card.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    @patch('integrabackend.payment.views.CreditCardViewSet.card_class')
    def test_cant_delete_credit_card(self, card_class):
        card_class.side_effect = azul.CantDeleteCard

        user = UserFactory()
        user.groups.add(GroupFactory(name='Aplicacion'))

        token, token_expiration, brand = azul.Card(
            number='4035874000424977',
            expiration='202012',
            cvc='977'
        ).validate(amount='100', code='CODE')
        
        credit_card = factories.CreditCardFactory(
            brand=brand,
            name='Name',
            data_vault_expiration=token_expiration,
            owner=self.user,
            token=token
        )

        response = self.client.delete('/api/v1/credit-card/%s/' % credit_card.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestPaymenetAttemptTestCase(APITestCase):

    def setUp(self):
        self.url = '/api/v1/payment-attempt/'
        self.keys_expect = [
            'sap_customer', 'date', 'id', 'invoices',
            'process_payment', 'transaction', 'user',
            'total_invoice_amount', 'total_invoice_tax'
        ]
        self.keys_expect_invoices = [
            'id', 'amount', 'amount_dop', 'company',
            'company_name', 'day_pass_due', 'description',
            'document_date', 'document_number', 'tax',
            'merchant_number', 'currency',
            'position', 'reference',
        ]
        self.user = UserFactory()
        self.resident = ResidentFactory(user=self.user, sap_customer=4259)
        self.payment_attempt = factories.PaymentAttemptFactory(user=self.resident.user)

    def test_can_list_payments_without_documents(self):
        self.client.force_authenticate(user=self.resident.user)
        response = self.client.get(self.url)

        for payment_attempt in response.json():
            for key in self.keys_expect:
                self.assertIn(key, payment_attempt)

    def test_only_list_request_user_payment_attempt(self):
        self.client.force_authenticate(user=self.resident.user)
        for _ in range(5):
            factories.PaymentAttemptFactory(user=UserFactory())

        response = self.client.get(self.url)

        self.assertEqual(len(response.json()), 1)

    def test_aplication_can_see_all(self):
        factories.PaymentAttemptFactory()
        self.assertNotEqual(models.PaymentAttempt.objects.count(), 1)

        aplication = UserFactory()
        aplication.groups.add(GroupFactory(name='Aplicacion'))
        self.client.force_login(user=aplication)

        self.assertTrue(aplication.is_aplication)

        response = self.client.get(self.url)

        self.assertNotEqual(len(response.json()), 1)

    def test_can_create_payments_attempt(self):
        # GIVE
        invoice_data = model_to_dict(
            factories.InvoiceFactory(),
            exclude=['payment_attempt', 'status', 'user'])

        data = model_to_dict(self.payment_attempt)
        data['invoices'] = [invoice_data]

        # WHEN
        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(self.url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in self.keys_expect:
            self.assertIn(key, response.json())

        status_invoice, _ = models.StatusDocument.objects.get_or_create(
            name="Pendiente"
        )

        for invoice in response.json().get('invoices'):
            for key in self.keys_expect_invoices:
                self.assertIn(key, invoice)
            self.assertEqual(invoice.get('status'), str(status_invoice.id))

    def test_not_send_correct_data(self):
        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.transaction_class')
    def test_transaction_invalid(self, transaction_class):
        transaction_response = MagicMock()
        transaction_response.response_code = '51'
        transaction_response.is_valid.return_value = False
        transaction_response.kwargs = {}

        transaction_class_mock = MagicMock()
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'number': '4035874000424977',
                'expiration': '202012',
                'cvc': '977',
                'save': False
            }
        }

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    @patch('integrabackend.payment.views.PaymentAttemptViewSet.transaction_class')
    def test_sap_raise_bad_request(self, transaction_class, compensation_payment):
        transaction_response = MagicMock()
        transaction_response.response_code = '00'
        transaction_response.authorization_code = 'OK200'
        transaction_response.data_vault_brand = 'VISA'
        transaction_response.data_vault_expiration = '202010'
        transaction_response.data_vault_token = 'TOKEN'

        transaction_class_mock = MagicMock()
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        compensation_payment_mock.commit.side_effect = BadRequest

        compensation_payment.return_value = compensation_payment_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'number': '4035874000424977',
                'expiration': '202012',
                'cvc': '977',
                'save': False
            }
        }

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        invoice.refresh_from_db()
        self.assertEqual(invoice.status.name, 'No Compensada')

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    @patch('integrabackend.payment.views.PaymentAttemptViewSet.transaction_class')
    def test_can_pay_payment_attempt_with_card_object(
            self, transaction_class, compensation_payment):

        transaction_response = MagicMock()
        transaction_response.response_code = '00'
        transaction_response.authorization_code = 'OK200'
        transaction_response.data_vault_brand = 'VISA'
        transaction_response.data_vault_expiration = '202010'
        transaction_response.data_vault_token = 'TOKEN'

        transaction_class_mock = MagicMock()
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'number': '4035874000424977',
                'expiration': '202012',
                'cvc': '977',
                'save': False
            }
        }

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.payment_attempt.refresh_from_db()

        self.assertEqual(invoice.payment_attempt.process_payment, 'AZUL')
        self.assertIsNotNone(invoice.payment_attempt.response)

        invoice.refresh_from_db()
        self.assertEqual(invoice.status.name, 'Compensada')

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    @patch('integrabackend.payment.views.PaymentAttemptViewSet.transaction_class')
    def test_can_pay_payment_attempt_with_save_true(
            self, transaction_class, compensation_payment):

        transaction_response = MagicMock()
        transaction_response.response_code = '00'
        transaction_response.authorization_code = 'OK200'
        transaction_response.data_vault_brand = 'VISA'
        transaction_response.data_vault_expiration = '202010'
        transaction_response.data_vault_token = 'TOKEN'

        transaction_class_mock = MagicMock()
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            "card": {
                "name": "Prueba",
                "number": "4035874000424977",
                "expiration": "202012",
                "cvc": "977",
                "save": True
            }
        }
        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment_attempt.refresh_from_db()

        self.assertEqual(self.payment_attempt.process_payment, 'AZUL')
        self.assertIsNotNone(self.payment_attempt.response)

        self.assertTrue(self.payment_attempt.user.credit_card.exists())
        self.assertTrue(self.user.credit_card.filter(name='Prueba').exists())

        invoice.refresh_from_db()
        self.assertEqual(invoice.status.name, 'Compensada')
    
    def test_cant_pay_payment_attempt_with_exists_response(self):
        payment_attempt = factories.PaymentAttemptFactory(
            user=self.resident.user
        )
        factories.ResponsePaymentAttempt(payment_attempt=payment_attempt)

        url = '/api/v1/payment-attempt/%s/charge/' % payment_attempt.id
        data = {
            "card": {
                "name": "Prueba",
                "number": "4035874000424977",
                "expiration": "202012", "cvc": "977",
            }
        }
        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')
    
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    @patch('integrabackend.payment.views.PaymentAttemptViewSet.transaction_class')
    def test_can_pay_payment_attempt_with_card_uuid(
            self, transaction_class, compensation_payment):

        transaction_response = MagicMock()
        transaction_response.response_code = '00'
        transaction_response.authorization_code = 'OK200'
        transaction_response.data_vault_brand = 'VISA'
        transaction_response.data_vault_expiration = '202010'
        transaction_response.data_vault_token = 'TOKEN'

        transaction_class_mock = MagicMock()
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        factories.CreditCardFactory(
            brand='VISA',
            name='Prueba',
            data_vault_expiration='202011',
            owner=self.payment_attempt.user,
            token='5EB29277-E93F-4D1F-867D-8E54AF97B86F')

        self.client.force_authenticate(user=self.resident.user)
        credit_card = self.client.get('/api/v1/credit-card/')

        self.assertEqual(credit_card.status_code, status.HTTP_200_OK)
        self.assertIn('id', credit_card.json()[0])
        self.assertIn('brand', credit_card.json()[0])
        self.assertIn('name', credit_card.json()[0])

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {'card_uuid': credit_card.json()[0].get('id')}

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment_attempt.refresh_from_db()

        self.assertEqual(self.payment_attempt.process_payment, 'AZUL')
        self.assertIsNotNone(self.payment_attempt.response)

        invoice.refresh_from_db()
        self.assertEqual(invoice.status.name, 'Compensada')
