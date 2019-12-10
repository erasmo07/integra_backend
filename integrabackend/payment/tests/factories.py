import factory
import random
import calendar
from integrabackend.users.test.factories import UserFactory


class PaymentAttemptFactory(factory.DjangoModelFactory):
    id = factory.Faker('uuid4')
    sap_customer = int("".join([str(random.randint(1, 9)) for _ in range(5)]))
    user = factory.SubFactory(UserFactory)
    
    class Meta:
        model = 'payment.PaymentAttempt'


class InvoiceFactory(factory.django.DjangoModelFactory):
    amount = 1.90
    amount_dop = 1.90
    currency = 'DOP'
    day_pass_due = '1'
    description = "".join([str(random.randint(1, 9)) for _ in range(5)])
    document_number = int("".join([str(random.randint(1, 9)) for _ in range(5)]))
    document_date = '2019-11-24' 
    merchant_number = "".join([str(random.randint(1, 9)) for _ in range(5)])
    payment_attempt = factory.SubFactory(PaymentAttemptFactory)
    position = "".join([str(random.randint(1, 9)) for _ in range(50)])
    reference = "".join([str(random.randint(1, 9)) for _ in range(50)])
    company = int("".join([str(random.randint(1, 9)) for _ in range(5)]))
    company_name = "".join([str(random.randint(1, 9)) for _ in range(50)])
    tax = 0.00


    class Meta:
        model = 'payment.Invoice'

