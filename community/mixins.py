from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication


class ApiAuthMixin:
    permission_classes = (IsAuthenticated,)


class ApiNoAuthMixin:
    permission_classes = (AllowAny,)
