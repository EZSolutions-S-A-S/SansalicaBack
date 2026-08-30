from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from inmuebles.composition import get_inmueble_repository
from inmuebles.domain.repositories import InmuebleRepository


class FakeRepository(InmuebleRepository):
    """Implementación mínima usada solo para verificar que composition.py
    resuelve la clase configurada en settings.INMUEBLE_REPOSITORY_CLASS."""

    def __init__(self, request=None):
        self.request = request

    def list(self, filters, page, page_size):
        raise NotImplementedError

    def get(self, inmueble_id):
        raise NotImplementedError

    def create(self, inmueble):
        raise NotImplementedError

    def update(self, inmueble_id, inmueble):
        raise NotImplementedError

    def delete(self, inmueble_id):
        raise NotImplementedError

    def add_photo(self, inmueble_id, image_file, order=0):
        raise NotImplementedError

    def delete_photo(self, photo_id):
        raise NotImplementedError


@override_settings(INMUEBLE_REPOSITORY_CLASS='test.inmuebles.test_composition.FakeRepository')
class GetInmuebleRepositoryTests(SimpleTestCase):
    def test_resolves_class_from_settings(self):
        repo = get_inmueble_repository()
        self.assertIsInstance(repo, FakeRepository)

    def test_passes_request_through(self):
        request = SimpleNamespace(id='fake-request')
        repo = get_inmueble_repository(request=request)
        self.assertIs(repo.request, request)

    def test_defaults_to_django_repository_from_real_settings(self):
        from inmuebles.infrastructure.repository import DjangoInmuebleRepository

        with self.settings(INMUEBLE_REPOSITORY_CLASS='inmuebles.infrastructure.repository.DjangoInmuebleRepository'):
            repo = get_inmueble_repository()
            self.assertIsInstance(repo, DjangoInmuebleRepository)
