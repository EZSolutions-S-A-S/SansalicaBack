import io
import os
import shutil
import tempfile
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from PIL import Image

from inmuebles.domain.entities import Inmueble, OperationType, PropertyType, Status
from inmuebles.domain.repositories import InmuebleFilters
from inmuebles.infrastructure.models import InmueblePhotoModel
from inmuebles.infrastructure.repository import DjangoInmuebleRepository

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix='sansalica-test-media-')
LOCAL_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def _inmueble(**overrides):
    data = dict(
        title='Casa en Zona 10',
        operation_type=OperationType.VENTA,
        property_type=PropertyType.CASA,
        price=Decimal('100000.00'),
        square_meters=Decimal('150.00'),
        location='Zona 10',
        description='Casa amplia con jardín',
    )
    data.update(overrides)
    return Inmueble(**data)


def _fake_image(name='foto.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (2, 2), color='red').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class DjangoInmuebleRepositoryCrudTests(TestCase):
    def setUp(self):
        self.repo = DjangoInmuebleRepository()

    def test_create_and_get(self):
        created = self.repo.create(_inmueble())
        self.assertIsNotNone(created.id)

        fetched = self.repo.get(created.id)
        self.assertEqual(fetched.title, 'Casa en Zona 10')
        self.assertEqual(fetched.status, Status.DISPONIBLE)

    def test_get_returns_none_when_missing(self):
        self.assertIsNone(self.repo.get(999999))

    def test_update_changes_fields(self):
        created = self.repo.create(_inmueble())
        updated = self.repo.update(created.id, _inmueble(title='Casa remodelada', price=Decimal('120000.00')))
        self.assertEqual(updated.title, 'Casa remodelada')
        self.assertEqual(updated.price, Decimal('120000.00'))

    def test_update_returns_none_when_missing(self):
        self.assertIsNone(self.repo.update(999999, _inmueble()))

    def test_delete_removes_row(self):
        created = self.repo.create(_inmueble())
        self.assertTrue(self.repo.delete(created.id))
        self.assertIsNone(self.repo.get(created.id))

    def test_delete_returns_false_when_missing(self):
        self.assertFalse(self.repo.delete(999999))


class DjangoInmuebleRepositoryFilterTests(TestCase):
    def setUp(self):
        self.repo = DjangoInmuebleRepository()
        self.venta_casa = self.repo.create(_inmueble(
            title='Casa en Zona 10', operation_type=OperationType.VENTA,
            property_type=PropertyType.CASA, price=Decimal('100000.00'), featured=True,
        ))
        self.alquiler_apto = self.repo.create(_inmueble(
            title='Apartamento en Zona 14', operation_type=OperationType.ALQUILER,
            property_type=PropertyType.APARTAMENTO, price=Decimal('5000.00'),
            location='Zona 14', featured=False,
        ))
        self.terreno = self.repo.create(_inmueble(
            title='Terreno en carretera al Salvador', operation_type=OperationType.VENTA,
            property_type=PropertyType.TERRENO, price=Decimal('250000.00'),
            location='Carretera al Salvador', status=Status.VENDIDO,
        ))

    def test_filter_by_operation_type(self):
        results, total = self.repo.list(InmuebleFilters(operation_type=OperationType.VENTA), 1, 20)
        self.assertEqual(total, 2)
        self.assertCountEqual([r.id for r in results], [self.venta_casa.id, self.terreno.id])

    def test_filter_by_property_type(self):
        results, total = self.repo.list(InmuebleFilters(property_type=PropertyType.APARTAMENTO), 1, 20)
        self.assertEqual(total, 1)
        self.assertEqual(results[0].id, self.alquiler_apto.id)

    def test_filter_by_status(self):
        results, total = self.repo.list(InmuebleFilters(status=Status.VENDIDO), 1, 20)
        self.assertEqual(total, 1)
        self.assertEqual(results[0].id, self.terreno.id)

    def test_filter_by_featured(self):
        results, total = self.repo.list(InmuebleFilters(featured=True), 1, 20)
        self.assertEqual(total, 1)
        self.assertEqual(results[0].id, self.venta_casa.id)

    def test_filter_by_price_range(self):
        results, total = self.repo.list(
            InmuebleFilters(min_price=Decimal('10000'), max_price=Decimal('150000')), 1, 20,
        )
        self.assertEqual(total, 1)
        self.assertEqual(results[0].id, self.venta_casa.id)

    def test_filter_by_search_matches_title_location_or_description(self):
        results, total = self.repo.list(InmuebleFilters(search='Zona 14'), 1, 20)
        self.assertEqual(total, 1)
        self.assertEqual(results[0].id, self.alquiler_apto.id)

    def test_ordering_by_price_ascending(self):
        results, _ = self.repo.list(InmuebleFilters(ordering='price'), 1, 20)
        prices = [r.price for r in results]
        self.assertEqual(prices, sorted(prices))

    def test_invalid_ordering_is_ignored_without_error(self):
        results, total = self.repo.list(InmuebleFilters(ordering='title'), 1, 20)
        self.assertEqual(total, 3)

    def test_pagination(self):
        results, total = self.repo.list(InmuebleFilters(), 1, 2)
        self.assertEqual(total, 3)
        self.assertEqual(len(results), 2)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT, STORAGES=LOCAL_STORAGES)
class DjangoInmuebleRepositoryPhotoTests(TestCase):
    """USE_R2_STORAGE=True en el .env real; estos tests fuerzan almacenamiento
    local temporal para no subir archivos de verdad a Cloudflare R2 en cada corrida."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.repo = DjangoInmuebleRepository()
        self.inmueble = self.repo.create(_inmueble())

    def test_add_photo_creates_row_and_returns_entity(self):
        photo = self.repo.add_photo(self.inmueble.id, _fake_image(), order=1)
        self.assertIsNotNone(photo)
        self.assertIsNotNone(photo.id)
        self.assertEqual(photo.order, 1)
        self.assertIsNotNone(photo.url)

    def test_add_photo_returns_none_for_missing_inmueble(self):
        photo = self.repo.add_photo(999999, _fake_image())
        self.assertIsNone(photo)

    def test_photo_appears_on_get(self):
        self.repo.add_photo(self.inmueble.id, _fake_image())
        fetched = self.repo.get(self.inmueble.id)
        self.assertEqual(len(fetched.photos), 1)

    def test_delete_photo_removes_row(self):
        photo = self.repo.add_photo(self.inmueble.id, _fake_image())
        self.assertTrue(self.repo.delete_photo(photo.id))
        fetched = self.repo.get(self.inmueble.id)
        self.assertEqual(len(fetched.photos), 0)

    def test_delete_photo_returns_false_when_missing(self):
        self.assertFalse(self.repo.delete_photo(999999))

    def test_delete_photo_removes_physical_file(self):
        photo = self.repo.add_photo(self.inmueble.id, _fake_image())
        model = InmueblePhotoModel.objects.get(id=photo.id)
        file_path = model.image.path
        self.assertTrue(os.path.exists(file_path))

        self.repo.delete_photo(photo.id)
        self.assertFalse(os.path.exists(file_path))

    def test_photo_url_without_request_is_relative(self):
        repo = DjangoInmuebleRepository(request=None)
        photo = repo.add_photo(self.inmueble.id, _fake_image())
        self.assertFalse(photo.url.startswith('http'))

    def test_photo_url_with_request_is_absolute(self):
        request = RequestFactory().get('/')
        repo = DjangoInmuebleRepository(request=request)
        photo = repo.add_photo(self.inmueble.id, _fake_image())
        self.assertTrue(photo.url.startswith('http'))
