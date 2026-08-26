from decimal import Decimal

from django.test import SimpleTestCase

from inmuebles.domain.entities import Inmueble, InmueblePhoto, OperationType, PropertyType, Status


class InmueblePhotoTests(SimpleTestCase):
    def test_defaults(self):
        photo = InmueblePhoto(url='https://example.com/a.jpg')
        self.assertEqual(photo.order, 0)
        self.assertIsNone(photo.id)

    def test_accepts_explicit_values(self):
        photo = InmueblePhoto(url=None, order=2, id=5)
        self.assertIsNone(photo.url)
        self.assertEqual(photo.order, 2)
        self.assertEqual(photo.id, 5)


class InmuebleDefaultsTests(SimpleTestCase):
    def _build(self, **overrides):
        data = dict(
            title='Casa de prueba',
            operation_type=OperationType.VENTA,
            property_type=PropertyType.CASA,
            price=Decimal('100000.00'),
            square_meters=Decimal('150.00'),
            location='Zona 10',
            description='Descripción',
        )
        data.update(overrides)
        return Inmueble(**data)

    def test_defaults(self):
        inmueble = self._build()
        self.assertIsNone(inmueble.id)
        self.assertEqual(inmueble.status, Status.DISPONIBLE)
        self.assertFalse(inmueble.featured)
        self.assertEqual(inmueble.features, [])
        self.assertEqual(inmueble.amenities, [])
        self.assertEqual(inmueble.photos, [])
        self.assertIsNone(inmueble.floor)
        self.assertIsNone(inmueble.bedrooms)

    def test_default_lists_are_independent_between_instances(self):
        first = self._build()
        second = self._build()
        first.features.append('piscina')
        self.assertEqual(second.features, [])


class EnumValuesTests(SimpleTestCase):
    def test_operation_type_values(self):
        self.assertEqual(OperationType.VENTA.value, 'Venta')
        self.assertEqual(OperationType.ALQUILER.value, 'Alquiler')

    def test_property_type_values(self):
        self.assertEqual(PropertyType.CASA.value, 'Casa')
        self.assertEqual(PropertyType.APARTAMENTO.value, 'Apartamento')
        self.assertEqual(PropertyType.LOCAL_COMERCIAL.value, 'Local Comercial')
        self.assertEqual(PropertyType.TERRENO.value, 'Terreno')

    def test_status_values(self):
        self.assertEqual(Status.DISPONIBLE.value, 'Disponible')
        self.assertEqual(Status.RESERVADO.value, 'Reservado')
        self.assertEqual(Status.VENDIDO.value, 'Vendido')

    def test_enum_members_behave_as_str(self):
        self.assertEqual(OperationType.VENTA, 'Venta')
        self.assertEqual(PropertyType.CASA, 'Casa')
