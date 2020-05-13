from rest_framework import permissions
from django.conf import settings
from . import enums


class OnlyUpdatePending(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method != 'PUT':
            return True

        is_pending = obj.status.name == enums.StatusInvitationEnums.pending
        return True if is_pending else False