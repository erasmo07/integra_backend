import factory
import random
import calendar
from integrabackend.users.test.factories import UserFactory


class ResponsePaymentAttempt(factory.DjangoModelFactory):
    id = factory.Faker('uuid4')
    response_code = '00'
    authorization_code = 'OK20202'
    order_id = '123'

    class Meta:
        model = 'payment.ResponsePaymentAttempt'


class PaymentAttemptFactory(factory.DjangoModelFactory):
    id = factory.Faker('uuid4')
    sap_customer = int("".join([str(random.randint(1, 9)) for _ in range(5)]))
    user = factory.SubFactory(UserFactory)
    merchant_number = '39038540035'
    merchant_name = 'CENREX'

    class Meta:
        model = 'payment.PaymentAttempt'


class StatusDocumentFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'payment.StatusDocument'


class InvoiceFactory(factory.django.DjangoModelFactory):
    amount = 0.75
    amount_dop = 39.38
    company = '0041'
    company_name = 'CTSPC'
    currency = 'DOP'
    day_pass_due = '1'
    description = "".join([str(random.randint(1, 9)) for _ in range(5)])
    document_date = '2019-11-24'
    document_number = '0900194811'
    merchant_number = '349052692'
    payment_attempt = factory.SubFactory(PaymentAttemptFactory)
    position = "".join([str(random.randint(1, 9)) for _ in range(50)])
    reference = "2000185388"
    status = factory.SubFactory(StatusDocumentFactory)
    tax = 0.00
    exchange_rate = '53.50'

    class Meta:
        model = 'payment.Invoice'


class AdvancePaymentFactory(factory.django.DjangoModelFactory):
    amount = 300.00
    bukrs = '0034'
    concept_id = '003'
    currency = 'DOP'
    description = 'Shool Down Payment'
    merchant_number = '1'
    payment_attempt = factory.SubFactory(PaymentAttemptFactory)
    position = "".join([str(random.randint(1, 9)) for _ in range(50)])
    spras = 'E'
    status = factory.SubFactory(StatusDocumentFactory)

    class Meta:
        model = 'payment.AdvancePayment'


class StatusCreditCardFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'payment.StatusCreditcard'


class CreditCardFactory(factory.django.DjangoModelFactory):
    status = factory.SubFactory(StatusCreditCardFactory)

    class Meta:
        model = 'payment.CreditCard'
