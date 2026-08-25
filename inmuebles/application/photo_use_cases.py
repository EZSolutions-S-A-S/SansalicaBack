from ..domain.entities import InmueblePhoto
from ..domain.repositories import InmuebleRepository


class AddInmueblePhoto:
    def __init__(self, repository: InmuebleRepository):
        self.repository = repository

    def execute(self, inmueble_id: int, image_file, order: int = 0) -> InmueblePhoto | None:
        return self.repository.add_photo(inmueble_id, image_file, order)


class DeleteInmueblePhoto:
    def __init__(self, repository: InmuebleRepository):
        self.repository = repository

    def execute(self, photo_id: int) -> bool:
        return self.repository.delete_photo(photo_id)
