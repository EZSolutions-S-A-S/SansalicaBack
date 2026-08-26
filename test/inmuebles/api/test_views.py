from decimal import Decimal

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from inmuebles.infrastructure.models import InmuebleModel

TEST_API_KEY = 'test-api-key'


@override_settings(READ_API_KEY=TEST_API_KEY)
class InmuebleViewSetPublicAccessTests(APITestCase):
    def setUp(self):
        self.list_url = '/api/inmuebles/'
        self.inmueble = InmuebleModel.objects.create(
            title='Casa en Zona 10', operation_type='Venta', property_type='Casa',
            price=Decimal('100000.00'), square_meters=Decimal('150.00'),
            location='Zona 10', description='desc',
        )

    def _auth_headers(self):
        return {'HTTP_AUTHORIZATION': f'Api-Key {TEST_API_KEY}'}

    def test_list_without_api_key_is_forbidden(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_wrong_api_key_is_forbidden(self):
        response = self.client.get(self.list_url, HTTP_AUTHORIZATION='Api-Key wrong-key')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_valid_api_key_succeeds(self):
        response = self.client.get(self.list_url, **self._auth_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_with_valid_api_key_succeeds(self):
        response = self.client.get(f'{self.list_url}{self.inmueble.id}/', **self._auth_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Casa en Zona 10')

    def test_create_with_api_key_but_no_staff_session_is_forbidden(self):
        payload = {
            'title': 'Nueva casa', 'operation_type': 'Venta', 'property_type': 'Casa',
            'price': '50000.00', 'square_meters': '90.00', 'location': 'Zona 1', 'description': 'desc',
        }
        response = self.client.post(self.list_url, payload, format='json', **self._auth_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_with_api_key_but_no_staff_session_is_forbidden(self):
        response = self.client.delete(f'{self.list_url}{self.inmueble.id}/', **self._auth_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(InmuebleModel.objects.filter(id=self.inmueble.id).exists())


@override_settings(READ_API_KEY=TEST_API_KEY)
class InmuebleViewSetQueryParamValidationTests(APITestCase):
    def setUp(self):
        self.list_url = '/api/inmuebles/'
        self.headers = {'HTTP_AUTHORIZATION': f'Api-Key {TEST_API_KEY}'}

    def test_invalid_page_returns_400_with_code(self):
        response = self.client.get(self.list_url, {'page': 'abc'}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_page')

    def test_invalid_page_size_returns_400_with_code(self):
        response = self.client.get(self.list_url, {'page_size': 'abc'}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_page_size')

    def test_invalid_min_price_returns_400_with_code(self):
        response = self.client.get(self.list_url, {'min_price': 'xyz'}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_price_range')

    def test_invalid_max_price_returns_400_with_code(self):
        response = self.client.get(self.list_url, {'max_price': 'xyz'}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_price_range')


@override_settings(READ_API_KEY=TEST_API_KEY)
class InmuebleViewSetFilteringTests(APITestCase):
    def setUp(self):
        self.list_url = '/api/inmuebles/'
        self.headers = {'HTTP_AUTHORIZATION': f'Api-Key {TEST_API_KEY}'}
        InmuebleModel.objects.create(
            title='Casa en venta', operation_type='Venta', property_type='Casa',
            price=Decimal('100000.00'), square_meters=Decimal('150.00'),
            location='Zona 10', description='desc',
        )
        InmuebleModel.objects.create(
            title='Apartamento en alquiler', operation_type='Alquiler', property_type='Apartamento',
            price=Decimal('5000.00'), square_meters=Decimal('60.00'),
            location='Zona 14', description='desc',
        )

    def test_filter_by_operation_type(self):
        response = self.client.get(self.list_url, {'operation_type': 'Alquiler'}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['operation_type'], 'Alquiler')

    def test_pagination_page_size(self):
        response = self.client.get(self.list_url, {'page_size': 1}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['count'], 2)
