from decimal import Decimal

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from inmuebles.api.errors import (
    ErrorCode,
    InvalidPageError,
    InvalidPageSizeError,
    InvalidPriceRangeError,
    MustBeNonNegative,
    MustBePositive,
    custom_exception_handler,
)


class ErrorCodeTests(SimpleTestCase):
    def test_values_are_english_snake_case(self):
        self.assertEqual(ErrorCode.INVALID_PAGE.value, 'invalid_page')
        self.assertEqual(ErrorCode.INVALID_PAGE_SIZE.value, 'invalid_page_size')
        self.assertEqual(ErrorCode.INVALID_PRICE_RANGE.value, 'invalid_price_range')
        self.assertEqual(ErrorCode.MUST_BE_POSITIVE.value, 'must_be_positive')
        self.assertEqual(ErrorCode.MUST_BE_NON_NEGATIVE.value, 'must_be_non_negative')


class InmuebleApiExceptionsTests(SimpleTestCase):
    def test_invalid_page_error_defaults(self):
        exc = InvalidPageError()
        self.assertEqual(exc.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exc.code, ErrorCode.INVALID_PAGE)

    def test_invalid_page_size_error_defaults(self):
        exc = InvalidPageSizeError()
        self.assertEqual(exc.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exc.code, ErrorCode.INVALID_PAGE_SIZE)

    def test_invalid_price_range_error_defaults(self):
        exc = InvalidPriceRangeError()
        self.assertEqual(exc.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exc.code, ErrorCode.INVALID_PRICE_RANGE)


class MustBePositiveTests(SimpleTestCase):
    def test_rejects_zero(self):
        validator = MustBePositive('must be positive')
        with self.assertRaises(ValidationError) as ctx:
            validator(Decimal('0'))
        self.assertEqual(ctx.exception.detail[0].code, ErrorCode.MUST_BE_POSITIVE.value)

    def test_rejects_negative(self):
        validator = MustBePositive('must be positive')
        with self.assertRaises(ValidationError):
            validator(Decimal('-1'))

    def test_accepts_positive(self):
        validator = MustBePositive('must be positive')
        validator(Decimal('0.01'))  # no debe lanzar


class MustBeNonNegativeTests(SimpleTestCase):
    def test_accepts_zero(self):
        validator = MustBeNonNegative('cannot be negative')
        validator(0)  # no debe lanzar

    def test_rejects_negative(self):
        validator = MustBeNonNegative('cannot be negative')
        with self.assertRaises(ValidationError) as ctx:
            validator(-1)
        self.assertEqual(ctx.exception.detail[0].code, ErrorCode.MUST_BE_NON_NEGATIVE.value)


class _DummyView(APIView):
    pass


class CustomExceptionHandlerTests(SimpleTestCase):
    def setUp(self):
        factory = APIRequestFactory()
        self.context = {'view': _DummyView(), 'request': factory.get('/'), 'args': (), 'kwargs': {}}

    def test_attaches_code_for_inmueble_api_exception(self):
        response = custom_exception_handler(InvalidPageError(), self.context)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_page')

    def test_attaches_code_for_field_validation_errors(self):
        try:
            MustBePositive('Price must be greater than 0.')(Decimal('-5'))
            self.fail('MustBePositive should have raised')
        except ValidationError as caught:
            exc = ValidationError({'price': caught.detail})

        response = custom_exception_handler(exc, self.context)
        self.assertEqual(response.data['price'][0]['code'], 'must_be_positive')
        self.assertEqual(response.data['price'][0]['message'], 'Price must be greater than 0.')

    def test_does_not_touch_unrelated_exceptions(self):
        # Guardia de regresión: los errores de auth/permisos deben renderizarse
        # exactamente como el manejador por defecto de DRF, sin 'code' agregado.
        response = custom_exception_handler(NotAuthenticated(), self.context)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('code', response.data)
