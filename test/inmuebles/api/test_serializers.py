from decimal import Decimal

from django.test import SimpleTestCase

from inmuebles.api.serializers import InmuebleSerializer
from inmuebles.domain.entities import Inmueble, OperationType, PropertyType, Status


def _valid_payload(**overrides):
    data = dict(
        title='Casa en venta',
        operation_type='Venta',
        property_type='Casa',
        price='100000.00',
        square_meters='150.00',
        location='Zona 10',
        description='Descripción',
    )
    data.update(overrides)
    return data


class InmuebleSerializerValidationTests(SimpleTestCase):
    def test_valid_payload_is_valid(self):
        serializer = InmuebleSerializer(data=_valid_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_price_zero_is_rejected(self):
        serializer = InmuebleSerializer(data=_valid_payload(price='0'))
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['price'][0].code, 'must_be_positive')

    def test_price_negative_is_rejected(self):
        serializer = InmuebleSerializer(data=_valid_payload(price='-1'))
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['price'][0].code, 'must_be_positive')

    def test_price_accepts_up_to_14_digits(self):
        serializer = InmuebleSerializer(data=_valid_payload(price='999999999999.99'))
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_square_meters_zero_is_rejected(self):
        serializer = InmuebleSerializer(data=_valid_payload(square_meters='0'))
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['square_meters'][0].code, 'must_be_positive')

    def test_bedrooms_negative_is_rejected(self):
        serializer = InmuebleSerializer(data=_valid_payload(bedrooms=-1))
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['bedrooms'][0].code, 'must_be_non_negative')

    def test_bedrooms_zero_is_allowed(self):
        serializer = InmuebleSerializer(data=_valid_payload(bedrooms=0))
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_bathrooms_negative_is_rejected(self):
        serializer = InmuebleSerializer(data=_valid_payload(bathrooms=-1))
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['bathrooms'][0].code, 'must_be_non_negative')

    def test_parking_spots_negative_is_rejected(self):
        serializer = InmuebleSerializer(data=_valid_payload(parking_spots=-1))
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['parking_spots'][0].code, 'must_be_non_negative')

    def test_floor_allows_negative_for_basements(self):
        serializer = InmuebleSerializer(data=_valid_payload(floor=-2))
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_photos_field_is_read_only_and_ignored_on_input(self):
        serializer = InmuebleSerializer(data=_valid_payload(photos=[{'url': 'x', 'order': 0}]))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn('photos', serializer.validated_data)


class InmuebleSerializerUpdateTests(SimpleTestCase):
    def _existing(self):
        return Inmueble(
            id=1, title='Original', operation_type=OperationType.VENTA,
            property_type=PropertyType.CASA, price=Decimal('100000'),
            square_meters=Decimal('150'), location='Zona 10', description='desc',
            status=Status.DISPONIBLE,
        )

    def test_partial_update_only_changes_sent_fields(self):
        instance = self._existing()
        serializer = InmuebleSerializer(instance, data={'price': '150000.00'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.price, Decimal('150000.00'))
        self.assertEqual(updated.title, 'Original')

    def test_partial_update_coerces_operation_type_to_enum(self):
        instance = self._existing()
        serializer = InmuebleSerializer(instance, data={'operation_type': 'Alquiler'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.operation_type, OperationType.ALQUILER)

    def test_partial_update_coerces_property_type_to_enum(self):
        instance = self._existing()
        serializer = InmuebleSerializer(instance, data={'property_type': 'Terreno'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.property_type, PropertyType.TERRENO)

    def test_partial_update_coerces_status_to_enum(self):
        instance = self._existing()
        serializer = InmuebleSerializer(instance, data={'status': 'Vendido'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.status, Status.VENDIDO)
