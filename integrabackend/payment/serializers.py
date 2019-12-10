from rest_framework import serializers
from . import models


class InvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Invoice
        fields = '__all__'
        read_only_fields = ('id', 'payment_attempt')


class AdvancePayment(serializers.ModelSerializer):

    class Meta:
        model = models.AdvancePayment
        fields = '__all__'
        read_only_fields = ('id', )


class PaymentAttemptSerializer(serializers.ModelSerializer):
    invoices = InvoiceSerializer(many=True)
    advancepayments = AdvancePayment(many=True, read_only=True)

    class Meta:
        model = models.PaymentAttempt
        fields = "__all__"
        read_only_fields = ('id', 'transaction', 'process_payment')
    
    def create(self, validated_data):
        invoices = validated_data.pop('invoices')
        payment_attempt = super(PaymentAttemptSerializer, self).create(validated_data)

        for invoice in invoices:
            invoice_serializer = InvoiceSerializer(data=invoice)
            invoice_serializer.is_valid(raise_exception=True)
            invoice_serializer.save(payment_attempt=payment_attempt)
        
        return payment_attempt