import io
import shutil
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from inmuebles.infrastructure.models import InmuebleModel

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix='sansalica-test-admin-media-')
LOCAL_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def _staff_user(username='admin-staff', password='clave-segura-123'):
    return User.objects.create_user(username=username, password=password, is_staff=True)


def _regular_user(username='agente', password='clave-segura-123'):
    return User.objects.create_user(username=username, password=password, is_staff=False)


def _fake_image(name='foto.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (2, 2), color='green').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class AdminAuthTests(APITestCase):
    def setUp(self):
        self.login_url = '/api/admin/auth/login/'
        self.refresh_url = '/api/admin/auth/refresh/'

    def test_staff_login_succeeds(self):
        _staff_user()
        response = self.client.post(
            self.login_url, {'username': 'admin-staff', 'password': 'clave-segura-123'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_non_staff_login_is_rejected(self):
        _regular_user()
        response = self.client.post(
            self.login_url, {'username': 'agente', 'password': 'clave-segura-123'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_credentials_are_rejected(self):
        _staff_user()
        response = self.client.post(
            self.login_url, {'username': 'admin-staff', 'password': 'incorrecta'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_returns_new_access_token(self):
        _staff_user()
        login_response = self.client.post(
            self.login_url, {'username': 'admin-staff', 'password': 'clave-segura-123'}, format='json',
        )
        refresh_response = self.client.post(
            self.refresh_url, {'refresh': login_response.data['refresh']}, format='json',
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)


class AdminInmuebleViewSetAuthorizationTests(APITestCase):
    def setUp(self):
        self.list_url = '/api/admin/inmuebles/'

    def test_anonymous_request_is_unauthorized(self):
        # Sin ningún autenticador exitoso, DRF devuelve 401 (NotAuthenticated) en vez
        # de 403 — la coerción a 403 solo aplica cuando SÍ hubo un autenticador exitoso
        # pero el permiso lo rechaza (ver test_non_staff_user_is_forbidden).
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_user_is_forbidden(self):
        self.client.force_authenticate(user=_regular_user())
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_create(self):
        self.client.force_authenticate(user=_staff_user())
        payload = {
            'title': 'Casa admin', 'operation_type': 'Venta', 'property_type': 'Casa',
            'price': '80000.00', 'square_meters': '120.00', 'location': 'Zona 1', 'description': 'desc',
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class AdminInmuebleViewSetCrudTests(APITestCase):
    def setUp(self):
        self.staff = _staff_user()
        self.client.force_authenticate(user=self.staff)
        self.list_url = '/api/admin/inmuebles/'
        self.inmueble = InmuebleModel.objects.create(
            title='Casa original', operation_type='Venta', property_type='Casa',
            price=Decimal('100000.00'), square_meters=Decimal('150.00'),
            location='Zona 10', description='desc',
        )
        self.detail_url = f'{self.list_url}{self.inmueble.id}/'

    def test_list_returns_created_inmueble(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_returns_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Casa original')

    def test_retrieve_missing_returns_404(self):
        response = self.client.get(f'{self.list_url}999999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_full_update_replaces_fields(self):
        payload = {
            'title': 'Casa actualizada', 'operation_type': 'Alquiler', 'property_type': 'Apartamento',
            'price': '3000.00', 'square_meters': '80.00', 'location': 'Zona 15', 'description': 'nueva desc',
        }
        response = self.client.put(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Casa actualizada')
        self.assertEqual(response.data['operation_type'], 'Alquiler')

    def test_partial_update_only_changes_sent_field(self):
        # Regresión: PATCH parcial no debe requerir (ni pisar) el resto de campos.
        response = self.client.patch(self.detail_url, {'price': '999.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['price'], '999.00')
        self.assertEqual(response.data['title'], 'Casa original')

    def test_delete_removes_inmueble(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(InmuebleModel.objects.filter(id=self.inmueble.id).exists())

    def test_delete_missing_returns_404(self):
        response = self.client.delete(f'{self.list_url}999999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminInmuebleViewSetQueryParamValidationTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(user=_staff_user())
        self.list_url = '/api/admin/inmuebles/'

    def test_invalid_page_returns_400_with_code(self):
        response = self.client.get(self.list_url, {'page': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_page')

    def test_invalid_page_size_returns_400_with_code(self):
        response = self.client.get(self.list_url, {'page_size': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_page_size')

    def test_invalid_max_price_returns_400_with_code(self):
        response = self.client.get(self.list_url, {'max_price': 'xyz'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'invalid_price_range')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT, STORAGES=LOCAL_STORAGES)
class AdminInmueblePhotoTests(APITestCase):
    """USE_R2_STORAGE=True en el .env real; estos tests fuerzan almacenamiento
    local temporal para no subir archivos de verdad a Cloudflare R2 en cada corrida."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client.force_authenticate(user=_staff_user())
        self.inmueble = InmuebleModel.objects.create(
            title='Casa con fotos', operation_type='Venta', property_type='Casa',
            price=Decimal('100000.00'), square_meters=Decimal('150.00'),
            location='Zona 10', description='desc',
        )
        self.photos_url = f'/api/admin/inmuebles/{self.inmueble.id}/photos/'

    def test_upload_photo_succeeds(self):
        response = self.client.post(self.photos_url, {'image': _fake_image(), 'order': 1}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['order'], 1)
        self.assertIsNotNone(response.data['url'])

    def test_upload_photo_for_missing_inmueble_returns_404(self):
        response = self.client.post(
            '/api/admin/inmuebles/999999/photos/', {'image': _fake_image()}, format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_photo_succeeds(self):
        upload_response = self.client.post(self.photos_url, {'image': _fake_image()}, format='multipart')
        photo_id = upload_response.data['id']
        delete_url = f'/api/admin/inmuebles/{self.inmueble.id}/photos/{photo_id}/'
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_missing_photo_returns_404(self):
        delete_url = f'/api/admin/inmuebles/{self.inmueble.id}/photos/999999/'
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
