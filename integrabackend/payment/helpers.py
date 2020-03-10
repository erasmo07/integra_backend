from datetime import datetime
from django.forms.models import model_to_dict
from oraculo.gods import sap


class CompensationPayment:
    sap_api = sap.APIClient
    sap_url = 'api_portal_clie/comp_factura'
    sap_response = None
    document_exclude_key = None 

    def __init__(self, transaction_attempt, language="S"):
        self.transaction_attempt = transaction_attempt
        self.language = language

        self.document_exclude_key = [
            'id', 'is_expired', 'day_pass_due',
            'payment_attempt', 'status', 'document_date'
        ]
        
        self.advance_exclude_key = [
            'id', 'payment_attempt', 'status']

    @property
    def customer(self):
        return self.transaction_attempt.user.resident.sap_customer
    
    @property
    def invoices(self):
        return self.transaction_attempt.invoices.all()
    
    @property
    def advancepayments(self):
        return self.transaction_attempt.advancepayments.all()
    
    def build_request_body(self):
        documents = list()
        for invoice in self.invoices:
            invoice_data = model_to_dict(invoice, exclude=self.document_exclude_key) 
            invoice_data['amount_dop'] = str(invoice_data['amount_dop'])
            invoice_data['amount'] = str(invoice_data['amount'])
            invoice_data['tax'] = str(invoice_data['tax'])
            invoice_data['exchange_rate'] = str(invoice_data['exchange_rate'])

            documents.append(invoice_data)
        
        advancepayments = list()
        for advance in self.advancepayments:
            advance_data = model_to_dict(advance, exclude=self.advance_exclude_key) 
            advance_data['amount'] = str(advance_data['amount'])
            advancepayments.append(advance_data)

        return dict(
            customer=self.customer,
            language=self.language,
            date=datetime.today().strftime('%Y%m%d'),
            datos_tranf=dict(
                id_transaction=self.transaction_attempt.transaction,
                cod_autorization=self.transaction_attempt.response.response_code
            ),
            invoice=documents,
            advancepayment=advancepayments,
        )

    def commit(self):
        sap_api = self.sap_api()
        self.sap_response = sap_api.post(self.sap_url, self.build_request_body())