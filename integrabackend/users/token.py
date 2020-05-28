from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import exceptions
from rest_framework.response import Response

from django.conf import settings
from django.shortcuts import get_object_or_404
from integrabackend.solicitude.views import get_value_or_404
from integrabackend.users import models


class CustomObtainAuthToken(ObtainAuthToken):
    message = 'This user does not have permission for this application'

    def post(self, request, *args, **kwargs):
        response = super(CustomObtainAuthToken, self).post(request, *args, **kwargs)

        token = Token.objects.get(key=response.data['token'])

        if settings.VALID_APPLICATION:
            key, application_id = request.META.get('HTTP_APPLICATION', ' ').split(' ')
            if key != 'Bifrost':
                raise exceptions.NotAuthenticated('Not send correct headers')

            _, application_id = request.META.get('HTTP_APPLICATION', ' ').split(' ')
            application = models.Application.objects.filter(id=application_id)
            if not application.exists():
                raise exceptions.NotAuthenticated('Applicaton not exists')


            has_access = token.user.accessapplication_set.filter(
                application__id=application_id).exists()
            if not has_access:
                detail = {
                    'detail': self.message,
                    'application': application.first().name}
                raise exceptions.NotAuthenticated(detail=detail)

        values = dict(token=token.key)
        if hasattr(token.user, 'resident'):
            values.update(dict(resident=token.user.resident.pk))
        
        default_client = token.user.accessapplication_set.filter(
            details__default=True).first() 
        if default_client:
            sap_customer = default_client.details.filter(
                default=True
            ).first().sap_customer
            values.update(dict(sap_customer=sap_customer))

        return Response(values)
    
    def get(self, request, *args, **kwargs):
        username = get_value_or_404(
            request.query_params,
            'username', 'Not send username')
        token = get_object_or_404(Token, user__username=username)

        values = dict(token=token.key)
        if hasattr(token.user, 'resident'):
            values.update(dict(resident=token.user.resident.pk))
        return Response(values)
