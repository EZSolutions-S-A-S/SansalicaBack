# Capa API — sistema de códigos de error para inmuebles/.
#
# El código HTTP (400, 403, etc.) ya tiene su propio "enum" bien establecido:
# rest_framework.status (y, por debajo, http.HTTPStatus de la librería estándar
# de Python). No se duplica eso aquí.
#
# Lo que SÍ falta y agrega este archivo es un segundo eje de información: dentro
# de un mismo código HTTP (ej. 400), *cuál* regla de negocio específica falló.
# Por eso ErrorCode es un enum aparte, no una copia de los códigos HTTP.

from enum import Enum

from rest_framework import serializers, status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


class ErrorCode(str, Enum):
    INVALID_PAGE = 'invalid_page'
    INVALID_PAGE_SIZE = 'invalid_page_size'
    INVALID_PRICE_RANGE = 'invalid_price_range'
    MUST_BE_POSITIVE = 'must_be_positive'
    MUST_BE_NON_NEGATIVE = 'must_be_non_negative'


# ---------------------------------------------------------------------------
# Excepciones para errores que ocurren ANTES de que exista un serializer al
# que "anidar" el error (parseo de query params en list()).
# ---------------------------------------------------------------------------

class InmuebleAPIException(APIException):
    """Base de las excepciones propias de inmuebles/ — todas cargan un ErrorCode."""

    code: ErrorCode

    def __init__(self, detail=None):
        super().__init__(detail=detail or self.default_detail)


class InvalidPageError(InmuebleAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The 'page' parameter must be a valid integer."
    code = ErrorCode.INVALID_PAGE


class InvalidPageSizeError(InmuebleAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The 'page_size' parameter must be a valid integer."
    code = ErrorCode.INVALID_PAGE_SIZE


class InvalidPriceRangeError(InmuebleAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The 'min_price' and 'max_price' parameters must be valid numbers."
    code = ErrorCode.INVALID_PRICE_RANGE


# ---------------------------------------------------------------------------
# Validadores reutilizables para reglas de negocio de campos del serializer.
# Se reusan en varios campos en vez de escribir un validate_<campo> por cada uno.
# ---------------------------------------------------------------------------

class MustBePositive:
    """Validador reusable: rechaza valores en cero o negativos."""

    def __init__(self, message: str):
        self.message = message

    def __call__(self, value):
        if value <= 0:
            raise serializers.ValidationError(self.message, code=ErrorCode.MUST_BE_POSITIVE.value)


class MustBeNonNegative:
    """Validador reusable: rechaza valores negativos (cero sí se permite)."""

    def __init__(self, message: str):
        self.message = message

    def __call__(self, value):
        if value < 0:
            raise serializers.ValidationError(self.message, code=ErrorCode.MUST_BE_NON_NEGATIVE.value)


# ---------------------------------------------------------------------------
# Exception handler — agrega "code" a la respuesta solo para nuestros propios
# tipos de error. No toca NotAuthenticated/PermissionDenied/AuthenticationFailed
# (ni ningún otro error que no sea de estos dos tipos), para no alterar el
# formato de respuesta de auth/permisos ya probado.
# ---------------------------------------------------------------------------

def _attach_codes(data):
    """Recorre recursivamente el detalle de un ValidationError y agrega el
    código de cada ErrorDetail individual, preservando el anidado por campo."""
    if isinstance(data, list):
        result = []
        for item in data:
            if isinstance(item, (dict, list)):
                result.append(_attach_codes(item))
            else:
                result.append({'message': str(item), 'code': getattr(item, 'code', None) or 'invalid'})
        return result
    if isinstance(data, dict):
        return {key: _attach_codes(value) for key, value in data.items()}
    return data


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    if isinstance(exc, InmuebleAPIException):
        response.data['code'] = exc.code.value
    elif isinstance(exc, ValidationError):
        response.data = _attach_codes(response.data)

    return response
