from datetime import datetime
from django.forms.models import model_to_dict
from oraculo.gods import sap
from partenon.process_payment import azul

from . import models


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


def save_request_to_azul(payment_attempt, transaction):
        azul_data = transaction.get_data()
        data = {azul.convert(key): value for key, value in azul_data.items()}

        data['card_number'] = data['card_number'][-4:]
        data['payment_attempt_id'] = payment_attempt.pk

        data.pop('cvc', None)
        data.pop('expiration', None)
        data.pop('data_vault_token', None)

        models.RequestPaymentAttempt.objects.create(**data)

def save_response_to_azul(
        payment_attempt, transaction_response,
        model=models.ResponsePaymentAttempt
    ):
    model.objects.create(
        payment_attempt=payment_attempt,
        response_code=transaction_response.response_code,
        authorization_code=transaction_response.authorization_code,
    )


def make_transaction_in_azul(
        payment_attempt,
        card,
        many='invoice',
        transaction_class=azul.Transaction,
        save_request=save_request_to_azul
    ):
    total = payment_attempt.total or "0.00"
    amount, amount_cents = str(total).split('.')

    taxs = getattr(payment_attempt, f'total_{many}_tax') or "0.00"
    tax, tax_cents = str(taxs).split('.')

    transaction = transaction_class(
        card=card,
        order_number=payment_attempt.transaction,
        amount="%s%s" % (amount, amount_cents),
        itbis="%s%s" % (tax, tax_cents),
        save_to_data_vault=None,
        merchan_name=payment_attempt.merchant_name,
        store=payment_attempt.merchant_number)

    save_request(payment_attempt, transaction)

    payment_attempt.process_payment = 'AZUL'
    payment_attempt.save()

    return transaction.commit()