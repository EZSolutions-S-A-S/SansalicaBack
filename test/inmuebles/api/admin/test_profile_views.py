import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from inmuebles.infrastructure.models import AdminProfileModel

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix='sansalica-test-profile-media-')
LOCAL_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def _staff_user(username='admin-staff', password='clave-segura-123'):
    return User.objects.create_user(username=username, password=password, is_staff=True)


def _fake_image(name='foto.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (2, 2), color='purple').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class AdminProfileViewAuthorizationTests(APITestCase):
    def test_requires_authentication(self):
        response = self.client.get('/api/admin/me/')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))


class AdminProfileViewTests(APITestCase):
    def setUp(self):
        self.staff = _staff_user()
        self.client.force_authenticate(user=self.staff)
        self.url = '/api/admin/me/'

    def test_get_creates_profile_if_missing(self):
        self.assertFalse(AdminProfileModel.objects.filter(user=self.staff).exists())

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AdminProfileModel.objects.filter(user=self.staff).exists())
        self.assertEqual(response.data['phone'], '')
        self.assertIsNone(response.data['photo_url'])

    def test_patch_updates_name_and_phone(self):
        response = self.client.patch(
            self.url, {'first_name': 'Andres', 'phone': '5555-1234'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Andres')
        self.assertEqual(response.data['phone'], '5555-1234')

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.first_name, 'Andres')

    def test_patch_only_changes_sent_fields(self):
        self.client.patch(self.url, {'first_name': 'Andres'}, format='json')
        response = self.client.patch(self.url, {'phone': '5555-1234'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Andres')
        self.assertEqual(response.data['phone'], '5555-1234')

    @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT, STORAGES=LOCAL_STORAGES)
    def test_patch_uploads_photo(self):
        response = self.client.patch(self.url, {'photo': _fake_image()}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['photo_url'])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class ChangePasswordViewTests(APITestCase):
    def setUp(self):
        self.staff = _staff_user(password='clave-actual-123')
        self.client.force_authenticate(user=self.staff)
        self.url = '/api/admin/me/change-password/'
        self.login_url = '/api/admin/auth/login/'

    def test_wrong_current_password_returns_400_with_code(self):
        response = self.client.post(
            self.url, {'current_password': 'incorrecta', 'new_password': 'nueva-clave-456'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['current_password'][0]['code'], 'invalid_current_password')

    def test_weak_new_password_is_rejected(self):
        response = self.client.post(
            self.url, {'current_password': 'clave-actual-123', 'new_password': '12345'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_correct_current_password_changes_it(self):
        response = self.client.post(
            self.url, {'current_password': 'clave-actual-123', 'new_password': 'nueva-clave-456'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        old_login = self.client.post(
            self.login_url, {'username': self.staff.username, 'password': 'clave-actual-123'}, format='json',
        )
        self.assertEqual(old_login.status_code, status.HTTP_401_UNAUTHORIZED)

        new_login = self.client.post(
            self.login_url, {'username': self.staff.username, 'password': 'nueva-clave-456'}, format='json',
        )
        self.assertEqual(new_login.status_code, status.HTTP_200_OK)
