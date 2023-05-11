from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser


class ApiAuthMixin:
    # ref. https://github.com/HackSoftware/Django-Styleguide-Example/blob/4a5b89ab3c5243d59db890b14f76e512d5c93a2a/README.md#drf--overriding-sessionauthentication
    # TODO: authentication_classes 추가

    # permission classes
    permission_classes = (IsAuthenticated,)


class ApiAdminAuthMixin:
    permission_classes = (IsAdminUser,)


class ApiAllowAnyMixin:
    permission_classes = (AllowAny,)
