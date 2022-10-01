<<<<<<< HEAD
from rest_framework.permissions import BasePermission, SAFE_METHODS

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
=======
from rest_framework.permissions import BasePermission


class IsSdpStaff(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.is_sdp:
                return True
        else:
            return False
>>>>>>> 1a1b26c89a8aff5a03dd199467db70ce80cd9432
