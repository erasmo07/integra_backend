# -*- coding: utf-8 -*-
from rest_framework import permissions
from integrabackend.solicitude import models
from partenon.ERP import ERPClient


class HasCreditPermission(permissions.BasePermission):
    message = 'Your credit status do not allow you to create new service requests.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if 'service' in request.data:
            service = models.Service.objects.get(pk=request.data.get('service'))
            if service.skip_credit_validation:
                return True

        try:
            resident = request.user.resident
            kwargs = {
                'client_code': resident.sap_customer,
            }
            erp_client = ERPClient(**kwargs)
            response = erp_client.has_credit()
            has_credit = response.get('puede_consumir')
            return has_credit
        except Exception as error:
            return True
