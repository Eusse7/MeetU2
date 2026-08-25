from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from apps.shared.domain.exceptions import DomainError


def domain_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response(
            {"error": {"codigo": exc.codigo, "mensaje": exc.mensaje}},
            status=exc.status_code,
        )
    return drf_exception_handler(exc, context)