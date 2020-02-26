import re
from rest_framework import serializers

from integrabackend.users.serializers import UserSerializer
from . import models



class ResponsePaymentAttemptSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ResponsePaymentAttempt
        fields = "__all__"
        read_only_fields = ('id', 'payment_attempt')


class CreditCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CreditCard
        exclude = ('token', )


class InvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Invoice
        fields = '__all__'
        read_only_fields = ('id', 'payment_attempt', 'status')


class AdvancePaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AdvancePayment
        fields = '__all__'
        read_only_fields = ('id', 'payment_attempt', 'status')


class PaymentAttemptSerializer(serializers.ModelSerializer):
    invoices = InvoiceSerializer(many=True)
    advancepayments = AdvancePaymentSerializer(many=True)
    response = ResponsePaymentAttemptSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    total_invoice_amount_usd = serializers.CharField(read_only=True)
    total_invoice_amount = serializers.CharField(read_only=True)
    total_invoice_tax = serializers.CharField(read_only=True)
    total_advancepayment_amount = serializers.CharField(read_only=True)
    total = serializers.CharField(read_only=True)

    class Meta:
        model = models.PaymentAttempt
        fields = "__all__"
        read_only_fields = ('id', 'transaction', 'process_payment', 'date')

    def create(self, validated_data):
        invoices = validated_data.pop('invoices')
        advancepayments = validated_data.pop('advancepayments')
        payment_attempt = super(PaymentAttemptSerializer, self).create(validated_data)

        status_pending, _ = models.StatusDocument.objects.get_or_create(
            name='Pendiente'
        )

        def make_many(serializer, data):
            serializer = serializer(data=data)
            serializer.is_valid(raise_exception=True)

            serializer.save(
                payment_attempt=payment_attempt,
                status=status_pending
            )

        for invoice in invoices:
            make_many(InvoiceSerializer, invoice)
        
        for advancepayment in advancepayments:
            make_many(AdvancePaymentSerializer, advancepayment)

        return payment_attempt


class PaymentAttemptPaySerializer(serializers.Serializer):
    number = serializers.CharField(min_length=16, max_length=16)
    expiration = serializers.CharField(max_length=6)
    cvc = serializers.CharField(max_length=4)
    save = serializers.BooleanField()

    def validate_number(self, value):
        PATTERN = '^([456][0-9]{3})(-?([0-9]{4}){3})$'
        """
        Stackexchange: 
            https://codereview.stackexchange.com/
                questions/169530/validating-credit-card-numbers
        By:
            https://codereview.stackexchange.com/users/21002/zeta

        Returns `True' if the sequence is a valid credit card number.

        A valid credit card number
        - must contain exactly 16 digits,
        - must start with a 4, 5 or 6 
        - must only consist of digits (0-9) or hyphens '-',
        - may have digits in groups of 4, separated by one hyphen "-". 
        - must NOT use any other separator like ' ' , '_',
        - must NOT have 4 or more consecutive repeated digits.
        """
        match = re.match(PATTERN, value)

        if match == None:
            raise serializers.ValidationError("Invalid Number")

        for group in match.groups():
            if group[0] * 4 == group:
                raise serializers.ValidationError("Invalid Number")
        return value
