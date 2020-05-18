from mock import patch, MagicMock
from datetime import datetime, timedelta

from django.forms.models import model_to_dict
from django.test import TransactionTestCase
from django.urls import reverse
from nose.tools import eq_, ok_
from rest_framework import status
from rest_framework.test import APITestCase

from oraculo.gods.exceptions import BadRequest
from partenon.process_payment import azul

from ...users.test.factories import UserFactory, GroupFactory
from integrabackend.resident.test.factories import ResidentFactory
from . import factories
from .. import models, enums


MOCK_REQUEST_TO_AZUL = {
    "AcquirerRefData": "1",
    "AltMerchantName": "CENREX",
    "Amount": "650730",
    "CardNumber": "999999xxxxxx9999",
    "Channel": "EC",
    "CurrencyPosCode": "$",
    "CustomerServicePhone": "809-111-2222",
    "ECommerceUrl": "www.miurl.com.do",
    "Itbis": "99264",
    "OrderNumber": 1,
    "Payments": "1",
    "Plan": "0",
    "PosInputMode": "E-Commerce",
    "SaveToDataVault": "0",
    "Store": "39038540035",
    "TrxType": "Sale",
}

MOCK_TRANSACTION_APROVE = {
    "AuthorizationCode": "OK463C",
    "AzulOrderId": "11350",
    "CustomOrderId": "ABC123",
    "DateTime": "20150206120821",
    "ErrorDescription": "",
    "IsoCode": "00",
    "LotNumber": "29",
    "RRN": "000012003029",
    "ResponseCode": "ISO8583",
    "ResponseMessage": "APROBADA",
    "Ticket": "2809"
}


class TestCreditCardTestCase(APITestCase):

    def setUp(self):
        self.keys_expects = [
            'id', 'brand', 'name', 'merchant_number',
            'card_number']

        self.user = UserFactory()
        factories.CreditCardFactory(
            brand='VISA',
            name='Name',
            data_vault_expiration='202011',
            owner=self.user,
            merchant_number='number',
            token='5EB29277-E93F-4D1F-867D-8E54AF97B86F')
        self.client.force_authenticate(user=self.user)

    def test_can_list_credit_card(self):
        credit_card = self.client.get('/api/v1/credit-card/')

        self.assertEqual(credit_card.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(credit_card.json()))

        for credit_card in credit_card.json():
            for key in self.keys_expects:
                self.assertIn(key, credit_card)

    def test_can_filter_credit_card(self):
        factories.CreditCardFactory(
            brand='VISA',
            name='Name',
            data_vault_expiration='202011',
            owner=self.user,
            merchant_number='second number',
            token='5EB29277-E93F-4D1F-867D-8E54AF97B86F')

        credit_card = self.client.get(
            '/api/v1/credit-card/',
            {'merchant_number': 'second number'})

        self.assertEqual(credit_card.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(credit_card.json()))

        for credit_card in credit_card.json():
            for key in self.keys_expects:
                self.assertIn(key, credit_card)

    def test_can_register_two_credit_card(self):
        factories.CreditCardFactory(
            brand='VISA', name='Name',
            data_vault_expiration='202011',
            merchant_number='number', owner=self.user,
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

        card = azul.Card(
            number='4035874000424977',
            expiration='202012',
            cvc='977'
        )

        transaction_response = azul.Transaction(
            card, '1000',
            merchan_name='CENREX',
            store='39038540035',
            save_to_data_vault='1').commit()

        credit_card = factories.CreditCardFactory(
            brand=transaction_response.data_vault_brand,
            name='Name',
            data_vault_expiration='202012',
            owner=self.user,
            token=transaction_response.data_vault_token,
            merchant_number='39038540035'
        )

        response = self.client.delete('/api/v1/credit-card/%s/' % credit_card.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @patch('integrabackend.payment.views.CreditCardViewSet.card_class')
    def test_cant_delete_credit_card(self, card_class):
        card_class.side_effect = azul.CantDeleteCard

        user = UserFactory()
        user.groups.add(GroupFactory(name='Aplicacion'))

        card = azul.Card(
            number='4035874000424977',
            expiration='202012',
            cvc='977'
        )

        transaction_response = azul.Transaction(
            card, '1000',
            merchan_name='CENREX',
            store='39038540035',
            save_to_data_vault='1').commit()

        credit_card = factories.CreditCardFactory(
            brand=transaction_response.data_vault_brand,
            name='Name',
            data_vault_expiration='202012',
            owner=self.user,
            token=transaction_response.data_vault_token,
            merchant_number='39038540035'
        )

        response = self.client.delete('/api/v1/credit-card/%s/' % credit_card.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestPaymenetAttemptTestCase(APITestCase, TransactionTestCase):

    def setUp(self):
        self.url = '/api/v1/payment-attempt/'
        self.keys_expect = [
            'sap_customer', 'date', 'id', 'invoices',
            'process_payment', 'transaction', 'user',
            'total_invoice_amount', 'total_invoice_tax',
            'total_advancepayment_amount', 'total',
            'status'
        ]

        self.keys_expect_invoices = [
            'id', 'amount', 'amount_dop', 'company',
            'company_name', 'day_pass_due', 'description',
            'document_date', 'document_number', 'tax',
            'merchant_number', 'currency',
            'position', 'reference',
        ]

        self.key_expect_advance_payment = [
            'bukrs', 'description', 'status', 'id',
            'concept_id', 'spras', 'amount',
        ]

        self.user = UserFactory()
        self.resident = ResidentFactory(user=self.user, sap_customer=4259)
        self.payment_attempt = factories.PaymentAttemptFactory(user=self.resident.user)

    def test_backoffice_can_list_payments(self):
        user = UserFactory()
        user.groups.add(GroupFactory(name='Backoffice'))

        self.client.force_authenticate(user=user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNot(len(response.json()), 0)

        for payment_attempt in response.json():
            for key in self.keys_expect:
                self.assertIn(key, payment_attempt)

    def test_backoffice_can_filte_one_day(self):
        user = UserFactory()
        user.groups.add(GroupFactory(name='Backoffice'))
        self.client.force_authenticate(user=user)

        for _ in range(5):
            factories.PaymentAttemptFactory.create()

        payment = factories.PaymentAttemptFactory.create()
        payment.date = datetime.today() + timedelta(2)
        payment.save()

        date = datetime.now() + timedelta(2)
        params = {
            'date_after': date.strftime("%Y-%m-%d"),
            'date_before': date.strftime("%Y-%m-%d")}
        response = self.client.get(self.url, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_backoffice_can_filte_by_status(self):
        user = UserFactory()
        user.groups.add(GroupFactory(name='Backoffice'))
        self.client.force_authenticate(user=user)

        for _ in range(5):
            factories.PaymentAttemptFactory.create()

        status_to_search = models.StatusPaymentAttempt.objects.create(name='TEST')

        payment = factories.PaymentAttemptFactory.create(status=status_to_search)

        params = {'status': str(status_to_search.id)}
        response = self.client.get(self.url, params)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_performance_list_payments_attempt(self):
        # GIVEN
        user = UserFactory()
        user.groups.add(GroupFactory(name='Backoffice'))
        self.client.force_authenticate(user=user)

        # THEN
        with self.assertNumQueries(5):
            response = self.client.get(self.url)

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
        data['advancepayments'] = []

        # WHEN
        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(self.url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in self.keys_expect:
            self.assertIn(key, response.json())

        payment_attempt = models.PaymentAttempt.objects.get(
            id=response.json().get('id'))

        self.assertEqual(
            payment_attempt.status.name,
            enums.StatusPaymentAttempt.initial)

        status_invoice, _ = models.StatusDocument.objects.get_or_create(
            name="Pendiente"
        )

        for invoice in response.json().get('invoices'):
            for key in self.keys_expect_invoices:
                self.assertIn(key, invoice)
            self.assertEqual(invoice.get('status'), str(status_invoice.id))

    def test_can_create_payments_attempt_with_sap_customer_name(self):
        # GIVE
        invoice_data = model_to_dict(
            factories.InvoiceFactory(),
            exclude=['payment_attempt', 'status', 'user'])

        data = model_to_dict(self.payment_attempt)
        data['sap_customer_name'] = 'PRUEBA'
        data['invoices'] = [invoice_data]
        data['advancepayments'] = []

        # WHEN
        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(self.url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in self.keys_expect:
            self.assertIn(key, response.json())

        payment_attempt = models.PaymentAttempt.objects.get(
            id=response.json().get('id'))

        self.assertEqual(
            payment_attempt.status.name,
            enums.StatusPaymentAttempt.initial)
        self.assertEqual(payment_attempt.sap_customer_name, "PRUEBA")

        status_invoice, _ = models.StatusDocument.objects.get_or_create(
            name="Pendiente"
        )
        for invoice in response.json().get('invoices'):
            for key in self.keys_expect_invoices:
                self.assertIn(key, invoice)
            self.assertEqual(invoice.get('status'), str(status_invoice.id))

    def test_can_create_payments_attempt_with_advance_payment(self):
        # GIVE
        invoice_data = model_to_dict(
            factories.InvoiceFactory(),
            exclude=['payment_attempt', 'status', 'user'])

        advance_payment = model_to_dict(
            factories.AdvancePaymentFactory(),
            exclude=['payment_attempt', 'status'])

        data = model_to_dict(self.payment_attempt)
        data['invoices'] = [invoice_data]
        data['advancepayments'] = [advance_payment]

        # WHEN
        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(self.url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in self.keys_expect:
            self.assertIn(key, response.json())

        payment_attempt = models.PaymentAttempt.objects.get(
            id=response.json().get('id'))
        self.assertEqual(
            payment_attempt.status.name,
            enums.StatusPaymentAttempt.initial)

        status_invoice, _ = models.StatusDocument.objects.get_or_create(
            name="Pendiente"
        )

        for invoice in response.json().get('invoices'):
            for key in self.keys_expect_invoices:
                self.assertIn(key, invoice)
            self.assertEqual(invoice.get('status'), str(status_invoice.id))

        for advance in response.json().get('advancepayments'):
            for key in self.key_expect_advance_payment:
                self.assertIn(key, advance)
            self.assertEqual(advance.get('status'), str(status_invoice.id))

        response_detail = self.client.get(
            "%s%s/" % (self.url, response.json().get('id')))

        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response_detail.json().get('total'),
            str(39.38 + 300.00))

        self.assertEqual(
            response_detail.json().get('total_invoice_amount'),
            str(39.38))

        self.assertEqual(
            response_detail.json().get('total_advancepayment_amount'),
            '300.00')

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
        transaction_class_mock.get_data.return_value = MOCK_REQUEST_TO_AZUL
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'cvc': '977',
                'expiration': '202012',
                'name': 'Prueba',
                'number': '4035874000424977',
                'save': False
            }
        }

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.payment_attempt.refresh_from_db()
        self.assertEqual(
            self.payment_attempt.card_number,
            data.get('card').get('number')[-4:])
        self.assertIsNotNone(self.payment_attempt.card_brand)

        self.assertEqual(
            self.payment_attempt.status.name,
            enums.StatusPaymentAttempt.not_approved)

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    def test_charge_payment_attempt_with_dinner_club(self, compensation_payment):
        # GIVEN
        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'cvc': '516',
                'expiration': '202406',
                'name': "Prueba",
                'number': '3643794964698356',
                'save': False
            }
        }

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json().keys(),
            MOCK_TRANSACTION_APROVE.keys())

        self.assertEqual(response.json().get('IsoCode'), '00')
        self.assertEqual(
            response.json().get('ResponseMessage'), 'APROBADA')

        invoice.refresh_from_db()
        invoice.payment_attempt.refresh_from_db()

        self.assertEqual(
            invoice.payment_attempt.status.name,
            enums.StatusPaymentAttempt.compensated)

        self.assertEqual(invoice.payment_attempt.process_payment, 'AZUL')
        self.assertEqual(
            invoice.payment_attempt.card_number,
            data.get('card').get('number')[-4:])

        self.assertIsNotNone(invoice.payment_attempt.response)

        self.assertEqual(
            invoice.status.name,
            enums.StatusInvoices.compensated)

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    def test_charge_payment_attempt_with_amex(self, compensation_payment):
        # GIVEN
        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'cvc': '274',
                'expiration': '202412',
                'name': 'Prueba',
                'number': '371642190784801',
                'save': False
            }
        }

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json().keys(),
            MOCK_TRANSACTION_APROVE.keys())

        self.assertEqual(response.json().get('IsoCode'), '00')
        self.assertEqual(
            response.json().get('ResponseMessage'), 'APROBADA')

        invoice.refresh_from_db()
        invoice.payment_attempt.refresh_from_db()

        self.assertEqual(
            invoice.payment_attempt.status.name,
            enums.StatusPaymentAttempt.compensated)

        self.assertEqual(invoice.payment_attempt.process_payment, 'AZUL')
        self.assertEqual(
            invoice.payment_attempt.card_number,
            data.get('card').get('number')[-4:])

        self.assertIsNotNone(invoice.payment_attempt.response)
        self.assertEqual(
            invoice.status.name,
            enums.StatusInvoices.compensated)

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    @patch('integrabackend.payment.views.PaymentAttemptViewSet.transaction_class')
    def test_can_pay_payment_attempt_american_express(
            self, transaction_class, compensation_payment):

        transaction_response = MagicMock()
        transaction_response.response_code = '00'
        transaction_response.authorization_code = 'OK200'
        transaction_response.data_vault_brand = 'VISA'
        transaction_response.data_vault_expiration = '202010'
        transaction_response.data_vault_token = 'TOKEN'
        transaction_response.kwargs = dict()

        transaction_class_mock = MagicMock()
        transaction_class_mock.get_data.return_value = MOCK_REQUEST_TO_AZUL
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        invoice = factories.InvoiceFactory(
            payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            "card": {
                "name": "Prueba",
                "number": "376695458359273",
                "expiration": "202012",
                "cvc": "977",
                "save": True
            }
        }
        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.json())
        self.payment_attempt.refresh_from_db()

        self.assertEqual(self.payment_attempt.process_payment, 'AZUL')
        self.assertEqual(
            self.payment_attempt.card_number,
            data.get('card').get('number')[-4:])

        self.assertIsNotNone(self.payment_attempt.response)

        self.assertTrue(self.payment_attempt.user.credit_card.exists())
        self.assertTrue(
            self.user.credit_card.filter(
                name='Prueba', card_number='9273'
            ).exists()
        )

        invoice.refresh_from_db()
        invoice.payment_attempt.refresh_from_db()

        self.assertEqual(invoice.status.name, 'Compensada')

        self.assertEqual(
            invoice.payment_attempt.status.name,
            enums.StatusPaymentAttempt.compensated)

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    @patch('integrabackend.payment.views.PaymentAttemptViewSet.transaction_class')
    def test_sap_raise_bad_request(self, transaction_class, compensation_payment):
        transaction_response = MagicMock()
        transaction_response.response_code = '00'
        transaction_response.authorization_code = 'OK200'
        transaction_response.data_vault_brand = 'VISA'
        transaction_response.data_vault_expiration = '202010'
        transaction_response.data_vault_token = 'TOKEN'
        transaction_response.kwargs = MOCK_TRANSACTION_APROVE

        transaction_class_mock = MagicMock()
        transaction_class_mock.get_data.return_value = MOCK_REQUEST_TO_AZUL
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        exception = BadRequest(
            '[{"error": [{"id": "F5", "znumber": 1, "message": "message"}]}]'
        )
        compensation_payment_mock.commit.side_effect = exception

        compensation_payment.return_value = compensation_payment_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'cvc': '977',
                'expiration': '202012',
                'name': "Prueba",
                'number': '4035874000424977',
                'save': False
            }
        }

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json().keys(),
            MOCK_TRANSACTION_APROVE.keys())

        invoice.refresh_from_db()

        self.assertEqual(
            invoice.status.name,
            enums.StatusInvoices.not_compensated)

        self.payment_attempt.refresh_from_db()

        self.assertEqual(
            self.payment_attempt.status.name,
            enums.StatusPaymentAttempt.not_compensated)

        self.assertEqual(
            self.payment_attempt.card_number,
            data.get('card').get('number')[-4:])

        self.assertTrue(self.payment_attempt.errors.filter(
            id_sap='F5', znumber=1, message='message'
        ).exists())

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
        transaction_response.kwargs = MOCK_TRANSACTION_APROVE

        transaction_class_mock = MagicMock()
        transaction_class_mock.get_data.return_value = MOCK_REQUEST_TO_AZUL
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'cvc': '977',
                'expiration': '202012',
                'name': 'Prueba',
                'number': '4035874000424977',
                'save': False
            }
        }

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json().keys(),
            MOCK_TRANSACTION_APROVE.keys())

        invoice.payment_attempt.refresh_from_db()

        self.assertEqual(invoice.payment_attempt.process_payment, 'AZUL')
        self.assertEqual(
            self.payment_attempt.card_number,
            data.get('card').get('number')[-4:])

        self.assertIsNotNone(invoice.payment_attempt.response)

        invoice.refresh_from_db()
        self.assertEqual(
            invoice.status.name,
            enums.StatusInvoices.compensated)

        self.payment_attempt.refresh_from_db()

        self.assertEqual(
            self.payment_attempt.status.name,
            enums.StatusPaymentAttempt.compensated)

    def test_backoffice_try_charge_payment(self):

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {
            'card': {
                'cvc': '977',
                'expiration': '202012',
                'name': 'Prueba',
                'number': '4035874000424977',
                'save': False
            }
        }

        user = UserFactory()
        user.groups.add(GroupFactory(name='Backoffice'))
        self.client.force_authenticate(user=user)

        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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
        transaction_response.kwargs = dict()

        transaction_class_mock = MagicMock()
        transaction_class_mock.get_data.return_value = MOCK_REQUEST_TO_AZUL
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
        self.assertIn('success', response.json())
        self.payment_attempt.refresh_from_db()

        self.assertEqual(self.payment_attempt.process_payment, 'AZUL')

        self.assertEqual(
            self.payment_attempt.status.name,
            enums.StatusPaymentAttempt.compensated)

        self.assertEqual(
            self.payment_attempt.card_number,
            data.get('card').get('number')[-4:])

        self.assertIsNotNone(self.payment_attempt.response)

        self.assertTrue(self.payment_attempt.user.credit_card.exists())
        self.assertTrue(
            self.user.credit_card.filter(
                name='Prueba', card_number='4977'
            ).exists()
        )

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
                "expiration": "202012",
                "cvc": "977",
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
        transaction_response.kwargs = dict()

        transaction_class_mock = MagicMock()
        transaction_class_mock.get_data.return_value = MOCK_REQUEST_TO_AZUL
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        credit_card = factories.CreditCardFactory(
            brand='VISA',
            name='Prueba',
            data_vault_expiration='202011',
            owner=self.payment_attempt.user,
            token='5EB29277-E93F-4D1F-867D-8E54AF97B86F')

        invoice = factories.InvoiceFactory(payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {'card_uuid': credit_card.id}

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get('success'))
        self.payment_attempt.refresh_from_db()

        self.assertEqual(self.payment_attempt.process_payment, 'AZUL')
        self.assertEqual(
            self.payment_attempt.card_number,
            credit_card.card_number)

        self.assertEqual(
            self.payment_attempt.status.name,
            enums.StatusPaymentAttempt.compensated)

        self.assertIsNotNone(self.payment_attempt.response)

        invoice.refresh_from_db()
        self.assertEqual(
            invoice.status.name,
            enums.StatusInvoices.compensated)

    @patch('integrabackend.payment.views.PaymentAttemptViewSet.compensation_payments')
    @patch('integrabackend.payment.views.PaymentAttemptViewSet.transaction_class')
    def test_can_pay_payment_attempt_with_advancepayment(
            self, transaction_class, compensation_payment):

        transaction_response = MagicMock()
        transaction_response.response_code = '00'
        transaction_response.authorization_code = 'OK200'
        transaction_response.data_vault_brand = 'VISA'
        transaction_response.data_vault_expiration = '202010'
        transaction_response.data_vault_token = 'TOKEN'
        transaction_response.kwargs = dict()

        transaction_class_mock = MagicMock()
        transaction_class_mock.get_data.return_value = MOCK_REQUEST_TO_AZUL
        transaction_class_mock.commit.return_value = transaction_response

        transaction_class.return_value = transaction_class_mock

        compensation_payment_mock = MagicMock()
        compensation_payment_mock.sap_response = {'data': 'PDF', 'success': True}

        compensation_payment.return_value = compensation_payment_mock

        credit_card = factories.CreditCardFactory(
            brand='VISA',
            name='Prueba',
            data_vault_expiration='202011',
            owner=self.payment_attempt.user,
            token='5EB29277-E93F-4D1F-867D-8E54AF97B86F',
            card_number='0000'
        )

        advancepayment = factories.AdvancePaymentFactory(
            payment_attempt=self.payment_attempt)
        url = '/api/v1/payment-attempt/%s/charge/' % self.payment_attempt.id
        data = {'card_uuid': credit_card.id}

        self.client.force_authenticate(user=self.resident.user)
        response = self.client.post(url, data, format='json')

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payment_attempt.refresh_from_db()
        self.assertEqual(self.payment_attempt.process_payment, 'AZUL')
        self.assertEqual(
            self.payment_attempt.card_number,
            credit_card.card_number)

        self.assertEqual(
            self.payment_attempt.status.name,
            enums.StatusPaymentAttempt.compensated)

        self.assertIsNotNone(self.payment_attempt.request)
        self.assertIsNotNone(self.payment_attempt.response)

        advancepayment.refresh_from_db()
        self.assertEqual(
            advancepayment.status.name,
            enums.StatusInvoices.compensated)
