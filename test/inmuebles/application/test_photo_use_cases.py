from django.test import SimpleTestCase

from inmuebles.application.photo_use_cases import AddInmueblePhoto, DeleteInmueblePhoto
from inmuebles.domain.entities import InmueblePhoto
from inmuebles.domain.repositories import InmuebleRepository


class FakePhotoRepository(InmuebleRepository):
    def __init__(self, photo=None, delete_result=True):
        self.calls = []
        self._photo = photo
        self._delete_result = delete_result

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
        self.calls.append(('add_photo', inmueble_id, image_file, order))
        return self._photo

    def delete_photo(self, photo_id):
        self.calls.append(('delete_photo', photo_id))
        return self._delete_result


class AddInmueblePhotoTests(SimpleTestCase):
    def test_delegates_to_repository_with_default_order(self):
        photo = InmueblePhoto(url='https://example.com/a.jpg', order=0, id=1)
        repo = FakePhotoRepository(photo=photo)
        result = AddInmueblePhoto(repo).execute(inmueble_id=7, image_file='file-stub')
        self.assertIs(result, photo)
        self.assertEqual(repo.calls, [('add_photo', 7, 'file-stub', 0)])

    def test_passes_custom_order(self):
        repo = FakePhotoRepository(photo=None)
        result = AddInmueblePhoto(repo).execute(inmueble_id=7, image_file='file-stub', order=3)
        self.assertIsNone(result)
        self.assertEqual(repo.calls, [('add_photo', 7, 'file-stub', 3)])


class DeleteInmueblePhotoTests(SimpleTestCase):
    def test_delegates_to_repository(self):
        repo = FakePhotoRepository(delete_result=True)
        result = DeleteInmueblePhoto(repo).execute(5)
        self.assertTrue(result)
        self.assertEqual(repo.calls, [('delete_photo', 5)])

    def test_returns_false_when_not_found(self):
        repo = FakePhotoRepository(delete_result=False)
        result = DeleteInmueblePhoto(repo).execute(999)
        self.assertFalse(result)
