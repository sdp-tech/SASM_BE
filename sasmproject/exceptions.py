# exception handling
from django.core.exceptions import ValidationError as DjangoValidationError, PermissionDenied
from django.http import Http404
from rest_framework.views import exception_handler
from rest_framework import exceptions
from rest_framework.serializers import as_serializer_error
from rest_framework.response import Response

from core.exceptions import ApplicationError


def custom_exception_handler(exc, ctx):
    """
    {
        "status": "fail",
        "message": "Error message",
        "extra": {
            ~~~
        }
    }
    """
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    if isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, ctx)

    # If unexpected error occurs (server error, etc.)
    if response is None:
        if isinstance(exc, ApplicationError):
            data = {
                "status": "fail",
                "message": exc.message,
                "extra": exc.extra
            }
            return Response(data, status=400)

        return response

    if isinstance(exc.detail, (list, dict)):
        response.data = {
            "status": "fail",
            "message": response.data
        }

    if isinstance(exc, exceptions.ValidationError):
        response.data = {
            "status": "fail",
            "message": "Validation error",
            "extra": {
                "fields": response.data["detail"]
            }
        }
    else:
        response.data = {
            "status": "fail",
            "message": response.data["detail"],
            "extra": {}
        }

    return response
