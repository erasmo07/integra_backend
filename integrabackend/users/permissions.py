from rest_framework import permissions
from django.conf import settings


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user



class ApplicationAuthorizeRest(permissions.BasePermission):
    header_key = 'HTTP_APPLICATION'

    def has_permission(self, request, view):
        if not settings.VALID_APPLICATION:
            return True

        header = request.META.get(self.header_key, ' ')
        
        key, application_id = header.split(' ')
        if key != 'Bifrost':
            return False

        try:
            return request.user.accessapplication_set.filter(
                application__id=application_id
            ).exists()
        except Exception as exception:
            return False


class IsApplicationUserPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        return request.user.is_aplication