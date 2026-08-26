from django.test import SimpleTestCase

from inmuebles.domain.repositories import InmuebleFilters, InmuebleRepository


class InmuebleFiltersTests(SimpleTestCase):
    def test_defaults_are_none(self):
        filters = InmuebleFilters()
        self.assertIsNone(filters.operation_type)
        self.assertIsNone(filters.property_type)
        self.assertIsNone(filters.status)
        self.assertIsNone(filters.featured)
        self.assertIsNone(filters.min_price)
        self.assertIsNone(filters.max_price)
        self.assertIsNone(filters.search)
        self.assertIsNone(filters.ordering)

    def test_stores_given_values(self):
        filters = InmuebleFilters(
            operation_type='Venta',
            property_type='Casa',
            status='Disponible',
            featured=True,
            min_price=100,
            max_price=200,
            search='zona 10',
            ordering='-price',
        )
        self.assertEqual(filters.operation_type, 'Venta')
        self.assertEqual(filters.property_type, 'Casa')
        self.assertEqual(filters.status, 'Disponible')
        self.assertTrue(filters.featured)
        self.assertEqual(filters.min_price, 100)
        self.assertEqual(filters.max_price, 200)
        self.assertEqual(filters.search, 'zona 10')
        self.assertEqual(filters.ordering, '-price')


class InmuebleRepositoryAbstractTests(SimpleTestCase):
    def test_cannot_instantiate_directly(self):
        with self.assertRaises(TypeError):
            InmuebleRepository()
