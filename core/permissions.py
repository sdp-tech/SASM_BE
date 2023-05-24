from rest_framework.permissions import BasePermission


class IsSdpStaff(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.is_sdp_admin:
                return True
        else:
            return False


class IsVerifiedOrSdpStaff(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.is_verified or request.user.is_sdp_admin:
                return True
        else:
            return False
