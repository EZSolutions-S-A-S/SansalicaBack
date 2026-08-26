import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.exceptions import AuthenticationFailed

from inmuebles.api.admin.serializers import InmueblePhotoUploadSerializer, StaffTokenObtainPairSerializer

User = get_user_model()


def _fake_image(name='foto.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (1, 1), color='blue').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class StaffTokenObtainPairSerializerTests(TestCase):
    def test_rejects_valid_credentials_for_non_staff_user(self):
        User.objects.create_user(username='agente', password='clave-segura-123', is_staff=False)
        serializer = StaffTokenObtainPairSerializer(data={'username': 'agente', 'password': 'clave-segura-123'})
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)

    def test_accepts_staff_user_and_returns_tokens(self):
        User.objects.create_user(username='admin-staff', password='clave-segura-123', is_staff=True)
        serializer = StaffTokenObtainPairSerializer(data={'username': 'admin-staff', 'password': 'clave-segura-123'})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIn('access', serializer.validated_data)
        self.assertIn('refresh', serializer.validated_data)

    def test_rejects_wrong_password(self):
        # simplejwt's own TokenObtainSerializer.validate() raises rest_framework's
        # base AuthenticationFailed here (not rest_framework_simplejwt's subclass).
        User.objects.create_user(username='admin-staff', password='clave-segura-123', is_staff=True)
        serializer = StaffTokenObtainPairSerializer(data={'username': 'admin-staff', 'password': 'incorrecta'})
        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)


class InmueblePhotoUploadSerializerTests(TestCase):
    def test_requires_image(self):
        serializer = InmueblePhotoUploadSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('image', serializer.errors)

    def test_order_defaults_to_zero(self):
        serializer = InmueblePhotoUploadSerializer(data={'image': _fake_image()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['order'], 0)

    def test_accepts_explicit_order(self):
        serializer = InmueblePhotoUploadSerializer(data={'image': _fake_image(), 'order': 3})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['order'], 3)
