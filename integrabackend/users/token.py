from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from integrabackend.solicitude.views import get_value_or_404


class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super(CustomObtainAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        values = dict(token=token.key)
        if hasattr(token.user, 'resident'):
            values.update(dict(resident=token.user.resident.pk))
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
