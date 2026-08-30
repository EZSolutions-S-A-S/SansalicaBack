from decimal import Decimal

from django.test import SimpleTestCase

from inmuebles.application.use_cases import (
    CreateInmueble,
    DeleteInmueble,
    GetInmueble,
    ListInmuebles,
    UpdateInmueble,
)
from inmuebles.domain.entities import Inmueble, OperationType, PropertyType
from inmuebles.domain.repositories import InmuebleFilters, InmuebleRepository


class FakeInmuebleRepository(InmuebleRepository):
    """Repositorio en memoria: registra las llamadas para poder verificar
    que cada caso de uso delega en el método correcto con los argumentos correctos."""

    def __init__(self):
        self.calls = []

    def list(self, filters, page, page_size):
        self.calls.append(('list', filters, page, page_size))
        return ([], 0)

    def get(self, inmueble_id):
        self.calls.append(('get', inmueble_id))
        return 'the-inmueble' if inmueble_id == 1 else None

    def create(self, inmueble):
        self.calls.append(('create', inmueble))
        return inmueble

    def update(self, inmueble_id, inmueble):
        self.calls.append(('update', inmueble_id, inmueble))
        return inmueble

    def delete(self, inmueble_id):
        self.calls.append(('delete', inmueble_id))
        return inmueble_id == 1

    def add_photo(self, inmueble_id, image_file, order=0):
        raise NotImplementedError

    def delete_photo(self, photo_id):
        raise NotImplementedError


def _sample_inmueble():
    return Inmueble(
        title='Casa',
        operation_type=OperationType.VENTA,
        property_type=PropertyType.CASA,
        price=Decimal('100'),
        square_meters=Decimal('50'),
        location='Zona 1',
        description='desc',
    )


class ListInmueblesTests(SimpleTestCase):
    def test_delegates_to_repository(self):
        repo = FakeInmuebleRepository()
        filters = InmuebleFilters()
        result = ListInmuebles(repo).execute(filters, page=2, page_size=10)
        self.assertEqual(result, ([], 0))
        self.assertEqual(repo.calls, [('list', filters, 2, 10)])


class GetInmuebleTests(SimpleTestCase):
    def test_delegates_to_repository(self):
        repo = FakeInmuebleRepository()
        result = GetInmueble(repo).execute(1)
        self.assertEqual(result, 'the-inmueble')
        self.assertEqual(repo.calls, [('get', 1)])

    def test_returns_none_when_missing(self):
        repo = FakeInmuebleRepository()
        result = GetInmueble(repo).execute(999)
        self.assertIsNone(result)


class CreateInmuebleTests(SimpleTestCase):
    def test_delegates_to_repository(self):
        repo = FakeInmuebleRepository()
        inmueble = _sample_inmueble()
        result = CreateInmueble(repo).execute(inmueble)
        self.assertIs(result, inmueble)
        self.assertEqual(repo.calls, [('create', inmueble)])


class UpdateInmuebleTests(SimpleTestCase):
    def test_delegates_to_repository(self):
        repo = FakeInmuebleRepository()
        inmueble = _sample_inmueble()
        result = UpdateInmueble(repo).execute(1, inmueble)
        self.assertIs(result, inmueble)
        self.assertEqual(repo.calls, [('update', 1, inmueble)])


class DeleteInmuebleTests(SimpleTestCase):
    def test_delegates_to_repository(self):
        repo = FakeInmuebleRepository()
        result = DeleteInmueble(repo).execute(1)
        self.assertTrue(result)
        self.assertEqual(repo.calls, [('delete', 1)])
