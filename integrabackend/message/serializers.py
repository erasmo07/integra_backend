from rest_framework import serializers
from . import models


class MessageSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()

    class Meta:
        model = models.Message
        fields = ['message']
        read_only = ['id', 'code']

    def get_message(self, obj):
        request = self.context.get('request')
        language = request.META.get('HTTP_ACCEPT_LANGUAGE')
        if not language:
            return obj[0].message
        return getattr(obj[0], 'message_%s' % language)
