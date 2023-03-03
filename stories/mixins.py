from rest_framework.permissions import IsAuthenticated

class ApiAuthMixin:
    permission_classes = (IsAuthenticated,)