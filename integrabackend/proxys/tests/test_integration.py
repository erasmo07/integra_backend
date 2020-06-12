from django.forms.models import model_to_dict
from django.test import TestCase, override_settings
from mock import MagicMock, patch
from rest_framework import status
from rest_framework.test import APITestCase

from integrabackend.payment.enums import StatusCompensation, StatusInvoices
from integrabackend.payment.tests.factories import (InvoiceFactory,
                                                    PaymentAttemptFactory)
from integrabackend.solicitude import helpers
from integrabackend.solicitude.tests.test_helpers import create_service_request
from integrabackend.users.test.factories import UserFactory
import random


class TestFaveoTicketDetailTestCase(APITestCase):
    
    def setUp(self):
        self.solicitude = create_service_request()
        helpers.create_service_request(self.solicitude)

        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_get_request_success(self):
        # WHEN
        response = self.client.get(
            '/api/v1/faveo/ticket/%s/' % self.solicitude.ticket_id)

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get('success'))


class TestERPClientViewSet(APITestCase):

    def setUp(self):
        self.url = '/api/v1/sap/client/4259/advance-payment/'
        
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    def test_advance_payment_get_request_success(self):
        # WHEN
        response = self.client.get(self.url, {'merchant': "349052692"})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for advance in response.json():
            self.assertIn('bukrs', advance)
            self.assertIn('concept_id', advance)
            self.assertIn('description', advance)
            self.assertIn('id', advance)
            self.assertIn('spras', advance)
            self.assertIn('status', advance)
    
    def test_society_get_request_success(self):
        # WHEN
        url = '/api/v1/sap/client/4259/society/'
        response = self.client.get(url, {'merchant': "349052692"})

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for advance in response.json():
            self.assertIn('company', advance)
            self.assertIn('company_name', advance)

    @patch('integrabackend.proxys.views.APIClientERP')
    def test_account_status_get_request_success(self, mock_erp_client):
        # Mock
        mock = MagicMock()
        mock.post.return_value = {'data': {}, 'success': True}
        mock_erp_client.return_value = mock

        # WHEN
        response = self.client.get(
            '/api/v1/sap/client/4259/account-status-pdf/',
            {
                "lang": "E",
                "merchant": "350000551",
                "date": "20200115"
            })

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.json())
        self.assertIn('success', response.json())

    @patch('integrabackend.proxys.views.ERPClient')
    def test_invoices_pdf_get_request_success(self, mock_erp_client):
        # Mock
        mock = MagicMock()

        mock_data = MagicMock()
        mock_data.data = 'DATA'

        mock.invoice_pdf.return_value = mock_data

        mock_erp_client.return_value = mock

        # WHEN
        response = self.client.get(
            '/api/v1/sap/client/9669/invoice-pdf/',
            {
                "lang": "S",
                "merchant": "39393850011",
                "document_number": "0900000001",
            })

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('binary', response.json())

        self.assertEqual(response.json(), {'binary': 'DATA'})

        mock.invoice_pdf.assert_called_once()
        mock.invoice_pdf.assert_called_once_with(
            '0900000001', '39393850011', language='S')
    
    @patch('integrabackend.proxys.views.ERPClient')
    def test_invoices_with_payment_attempt_not_compensated(self, mock_erp_client):
        # GIVEN
        not_compensated = StatusCompensation.not_compensated
        invoice = InvoiceFactory.create(
            status__name=StatusInvoices.not_compensated,
            payment_attempt__status_compensation__name=not_compensated)
        
        mock = MagicMock()
        mock_data = MagicMock()
        mock_data._base = model_to_dict(invoice, exclude=['id'])

        mock.invoices.return_value = [mock_data]

        mock_erp_client.return_value = mock

        # WHEN
        response = self.client.get(
            f'/api/v1/sap/client/{invoice.payment_attempt.sap_customer}/invoices/',
            {
                "lang": "S",
                "merchant": "39393850011",
            })
        
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)
    
    @patch('integrabackend.proxys.views.ERPClient')
    def test_invoice_exclude_only_one(self, mock_erp_client):
        # GIVEN
        sap_customer = '0007'
        invoices = list()
        for _ in range(5):
            mock_data = MagicMock()
            mock_data._base = model_to_dict(
                InvoiceFactory.create(),
                exclude=['id', 'status', 'payment_attempt'])
            invoices.append(mock_data)
        
        invoice_not_include = InvoiceFactory.create(
            document_number=invoices[random.randint(0, 4)]._base.get('document_number'),
            status__name=StatusInvoices.not_compensated,
            payment_attempt__sap_customer=sap_customer,
            payment_attempt__status_compensation__name=StatusCompensation.not_compensated)

        mock = MagicMock()
        mock.invoices.return_value = invoices

        mock_erp_client.return_value = mock

        # WHEN
        response = self.client.get(
            f'/api/v1/sap/client/{sap_customer}/invoices/',
            {
                "lang": "S",
                "merchant": "39393850011",
            })
        
    
        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 4)

        for invoice in response.json():
            self.assertNotEqual(
                invoice.get('document_number'),
                invoice_not_include.document_number
            )


class TestTemporalInvoice(APITestCase):
    
    def setUp(self):
        self.url = '/api/v1/sap/temporal-invoice/'
        
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    @patch('integrabackend.proxys.views.APIClientERP')
    def test_generic_path(self, mock_api_client):
        body = {
            "CLIENTE_SAP" : "ESPVFISCAL",   
            "CLIENTE_ESPORADICO" : [ "NOMBRE", "0980897897" ],
            "CANAL_DISTRIBUCION" : "02",
            "POSICION" : [{
                "COMENTARIO" : "Uso privado salon VIP CAE",
                "KMEIN" : "",
                "KPEIN" : "3",
                "MATNR" : "000000000009000320",
            }]
        }

        mock = MagicMock()
        mock.post.return_value = {}
        mock_api_client.return_value = mock

        response = self.client.post(self.url, body)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
