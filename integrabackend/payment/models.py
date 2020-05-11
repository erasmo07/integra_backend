import uuid
import decimal
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from . import enums


class Status(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=50)

    class Meta:
        abstract = True

    def __unicode__(self):
        """Unicode representation of StatusDocument."""
        return self.name


class StatusDocument(Status):
    pass


class StatusCreditcard(Status):
    pass


class StatusPaymentAttempt(Status):
    pass


class CreditCard(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    token = models.CharField(max_length=100)
    status = models.ForeignKey(
        "payment.StatusCreditCard", on_delete=models.CASCADE)
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE, related_name='credit_card')
    brand = models.CharField('Brand', max_length=10)
    card_number = models.CharField('Card Number', max_length=4)
    data_vault_expiration = models.CharField(
        'DataVaultExpiration', max_length=6)
    merchant_number = models.CharField('Merchant', max_length=50)


class ResponsePaymentAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_attempt = models.OneToOneField(
        "payment.PaymentAttempt",
        on_delete=models.DO_NOTHING,
        related_name='response')
    date = models.DateTimeField('Create DateTime', auto_now_add=True)
    response_code = models.CharField('Response Code', max_length=10)
    authorization_code = models.CharField('Authorization Code', max_length=10)
    order_id = models.CharField('Order ID', max_length=10)


class RequestPaymentAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_attempt = models.OneToOneField(
        "payment.PaymentAttempt",
        on_delete=models.DO_NOTHING,
        related_name='request')
    acquirer_ref_data = models.CharField(
        'AquirerRefData', max_length=50)
    alt_merchant_name = models.CharField(
        'AltMerchantName', max_length=50)
    amount = models.CharField('Amount', max_length=50)
    card_number = models.CharField(
        'CardNumber', max_length=4)
    channel = models.CharField(
        'Channel', max_length=50)
    currency_pos_code = models.CharField(
        'CurrencyPosCode', max_length=50)
    customer_service_phone = models.CharField(
        'CustomerServicePhone', max_length=50)
    date = models.DateTimeField(
        'Create DateTime', auto_now_add=True)
    e_commerce_url = models.CharField(
        'ECommerUrl', max_length=250)
    itbis = models.CharField('ITBIS', max_length=50)
    order_number = models.IntegerField()
    payments = models.CharField('Payments', max_length=50)
    plan = models.CharField('Plan', max_length=50)
    pos_input_mode = models.CharField(
        'PostInputMode', max_length=50)
    store = models.CharField('Store', max_length=50)
    trx_type = models.CharField('TrxType', max_length=50)
    save_to_data_vault = models.CharField(
        'SaveToDataVault', max_length=50)


class ErrorPaymentAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_attempt = models.ForeignKey(
        'payment.PaymentAttempt',
        related_name='errors',
        on_delete=models.CASCADE)
    id_sap = models.CharField(max_length=5)
    znumber = models.IntegerField()
    message = models.TextField()


class PaymentAttempt(models.Model):
    """Model definition for StatusDocument. """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sap_customer = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    process_payment = models.CharField(
        'Process Payment',
        max_length=50,
        blank=True, null=True
    )
    transaction = models.IntegerField()
    card_number = models.CharField(
        'Card Number', max_length=4, blank=True, null=True)

    merchant_number = models.CharField(
        'Merchant Number', max_length=50, blank=True, null=True)
    merchant_name = models.CharField(
        'Merchant Name', max_length=50, blank=True, null=True)
    
    total_invoice_amount = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    total_advancepayment_amount = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    total_invoice_tax = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    total_invoice_amount_usd = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)

    user = models.ForeignKey("users.User", on_delete=models.DO_NOTHING, null=True)
    status = models.ForeignKey(
        "payment.StatusPaymentAttempt",
        on_delete=models.CASCADE, blank=True, null=True)

    @property
    def total(self):
        invoice = self.total_invoice_amount
        if not invoice:
            invoice = decimal.Decimal(0.00)

        advancepayment = self.total_advancepayment_amount
        if not advancepayment:
            advancepayment = decimal.Decimal(0.00)

        return invoice + advancepayment
    
    def get_total(self, foreign_key, field):
        total = getattr(self, foreign_key).values(
            field
        ).aggregate(total=models.Sum(field)).get('total', 0)
        return total if total else decimal.Decimal(0.00)

    def save(self, *args, **kwargs):
        last = PaymentAttempt.objects.order_by('transaction').last()
        if not last:
            self.transaction = 1
        else:
            self.transaction = last.transaction + 1
        
        self.total_invoice_amount = self.get_total('invoices', 'amount_dop')
        self.total_advancepayment_amount = self.get_total('advancepayments', 'amount')
        self.total_invoice_tax = self.get_total('invoices', 'tax')
        self.total_invoice_amount_usd = self.get_total('invoices', 'amount')

        return super(PaymentAttempt, self).save(*args, **kwargs)


class PaymentDocument(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    currency = models.CharField('Currency', max_length=3)
    position = models.CharField('Position', max_length=50)
    merchant_number = models.CharField(max_length=50)

    payment_attempt = models.ForeignKey(
        'payment.PaymentAttempt',
        related_name='%(class)ss',
        on_delete=models.CASCADE
    )

    status = models.ForeignKey(
        "payment.StatusDocument",
        on_delete=models.DO_NOTHING,
        limit_choices_to={
            'name__in': [
                enums.StatusInvoices.compensated,
                enums.StatusInvoices.not_compensated
            ]
        }
    )

    class Meta:
        abstract = True


class Invoice(PaymentDocument):
    amount_dop = models.DecimalField(max_digits=10, decimal_places=2)
    company = models.IntegerField('Company')
    company_name = models.CharField('Company Name', max_length=50)
    date = models.DateTimeField(auto_now_add=True)
    day_pass_due = models.CharField('Day pass due', max_length=50)
    document_date = models.DateField('Document Date')
    document_number = models.BigIntegerField('Document Number')
    reference = models.CharField("Reference", max_length=50)
    tax = models.DecimalField('Tax', max_digits=10, decimal_places=2)
    exchange_rate = models.DecimalField(
        'Exchange rate', max_digits=7, decimal_places=5)


class AdvancePayment(PaymentDocument):
    concept_id = models.CharField('Concept', max_length=50)
    spras = models.CharField('Spras', max_length=1)
    bukrs = models.CharField('Bukrs', max_length=50)
