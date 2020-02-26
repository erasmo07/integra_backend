from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.exceptions import (
    APIException, NotFound, ParseError, PermissionDenied)
from rest_framework.response import Response

from oraculo.gods.exceptions import BadRequest
from partenon.process_payment import azul

from ..users.models import User
from ..solicitude.serializers import StateSerializer
from . import helpers, models, serializers, enums, filters
from .helpers import CompensationPayment


class CreditCardViewSet(
        viewsets.ReadOnlyModelViewSet,
        generics.DestroyAPIView):
    queryset = models.CreditCard.objects.all()
    serializer_class = serializers.CreditCardSerializer
    filter_backends = [DjangoFilterBackend]
    filter_fields = ['owner',]
    card_class = azul.Card

    def get_queryset(self):
        queryset = super(CreditCardViewSet, self).get_queryset()
        if self.request.user.is_aplication:
            return queryset 
        return queryset.filter(owner=self.request.user) 
    
    def perform_destroy(self, instance):
        try:
            self.card_class(instance.token).delete()
            return super(CreditCardViewSet, self).perform_destroy(instance)
        except azul.CantDeleteCard as exception:
            raise ParseError(detail='Cant delete credit card')


class StatePaymentDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List PaymentAttempt's status
    """
    queryset = models.StatusDocument.objects.filter(
        name__in=[
            enums.StatusInvoices.compensated,
            enums.StatusInvoices.not_compensated
        ])
    serializer_class = StateSerializer


class PaymentAttemptViewSet(viewsets.ModelViewSet):
    """
    Create resident
    """
    queryset = models.PaymentAttempt.objects.all()
    serializer_class = serializers.PaymentAttemptSerializer
    serialiser_pay_class = serializers.PaymentAttemptPaySerializer
    card_class = azul.Card
    transaction_class = azul.Transaction
    response_payment_attemp_model = models.ResponsePaymentAttempt
    credit_card_model = models.CreditCard
    compensation_payments = CompensationPayment
    filter_backends = [DjangoFilterBackend]
    filter_class = filters.PaymentAttemptFilter

    def get_queryset(self):
        queryset = super(PaymentAttemptViewSet, self).get_queryset()
        if (
                self.request.user.is_aplication
                or self.request.user.is_backoffice
            ):
            return queryset
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.is_aplication and 'user' not in self.request.data:
            raise NotFound(detail='User is aplication need to set user key')
        
        if self.request.user.is_aplication and 'user' in self.request.data:
            serializer.save(user=get_object_or_404(User, self.request.data))
            return

        serializer.save(user=self.request.user)

    def get_azul_card(self):
        if 'card' in self.request.data:
            serializer = self.serialiser_pay_class(data=self.request.data.get('card'))
            serializer.is_valid(raise_exception=True)

            return self.card_class(
                number=serializer.data.get('number'),
                expiration=serializer.data.get('expiration'),
                cvc=serializer.data.get('cvc'))

        if 'card_uuid' in self.request.data:
            card_uuid = self.request.data.get('card_uuid')
            credit_card = get_object_or_404(self.credit_card_model, id=card_uuid)

            return self.card_class(token=credit_card.token)
        raise NotFound(detail="Not send card correct structure")

    def make_transaction_in_azul(self):
        total = self.object.total or "0.00"
        amount, amount_cents = str(total).split('.')

        taxs = self.object.total_invoice_tax or "0.00"
        tax, tax_cents = str(taxs).split('.')

        save_data_vault = '1' if self.request.data.get('card', {}).get('save') else None
        transaction = self.transaction_class(
            card=self.get_azul_card(),
            order_number=self.object.transaction,
            amount="%s%s" % (amount, amount_cents),
            itbis="%s%s" % (tax, tax_cents),
            save_to_data_vault=save_data_vault)

        self.object.process_payment = 'AZUL'
        self.object.save()
        return transaction.commit()

    def save_credit_card(self, transaction_response):
        status, _ = models.StatusCreditcard.objects.get_or_create(
            name='Valida'
        )

        self.credit_card_model.objects.create(
            brand=transaction_response.data_vault_brand,
            data_vault_expiration=transaction_response.data_vault_expiration,
            owner=self.object.user,
            status=status,
            token=transaction_response.data_vault_token,
            name=self.request.data.get('card', {}).get('name')
        )

    @action(detail=True, methods=['POST'])
    def charge(self, request, pk=None):
        if self.request.user.is_backoffice:
            raise PermissionDenied(detail="User can't charge payment") 

        self.object = self.get_object()
        if hasattr(self.object, 'response'):
            raise ParseError(detail='PaymentAttempt has one response')

        transaction_response = self.make_transaction_in_azul()
        if not transaction_response.is_valid():
            return Response(transaction_response.kwargs, status=400)

        self.response_payment_attemp_model.objects.create(
            payment_attempt=self.object,
            response_code=transaction_response.response_code,
            authorization_code=transaction_response.authorization_code,
        )

        try:
            compensation_payment = self.compensation_payments(self.object)
            compensation_payment.commit()
        except BadRequest as exception:
            status, _ = models.StatusDocument.objects.get_or_create(
                name=enums.StatusInvoices.not_compensated
            )
            self.object.invoices.update(status=status)
            raise NotFound(detail='SAP return 500 not charge invoice')

        status, _ = models.StatusDocument.objects.get_or_create(
            name=enums.StatusInvoices.compensated
        )
        self.object.invoices.update(status=status)
        self.object.advancepayments.update(status=status)

        if (transaction_response.is_valid()
                and self.request.data.get('card', {}).get('save')):
            self.save_credit_card(transaction_response)
        return Response(compensation_payment.sap_response)
