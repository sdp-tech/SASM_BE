from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsWriter(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'writer'):
            return obj.writer.id == request.user.id
        return True