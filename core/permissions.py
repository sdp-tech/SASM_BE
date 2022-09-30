from rest_framework.permissions import BasePermission


class IsSdpStaff(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.is_sdp:
                return True
        else:
            return False
