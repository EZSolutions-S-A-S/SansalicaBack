from abc import ABC, abstractmethod

from .entities import Inmueble, InmueblePhoto


class InmuebleFilters:
    def __init__(
        self,
        operation_type=None,
        property_type=None,
        status=None,
        featured=None,
        min_price=None,
        max_price=None,
        search=None,
        ordering=None,
    ):
        self.operation_type = operation_type
        self.property_type = property_type
        self.status = status
        self.featured = featured
        self.min_price = min_price
        self.max_price = max_price
        self.search = search
        self.ordering = ordering


class InmuebleRepository(ABC):
    @abstractmethod
    def list(self, filters: InmuebleFilters, page: int, page_size: int) -> tuple[list[Inmueble], int]: ...

    @abstractmethod
    def get(self, inmueble_id: int) -> Inmueble | None: ...

    @abstractmethod
    def create(self, inmueble: Inmueble) -> Inmueble: ...

    @abstractmethod
    def update(self, inmueble_id: int, inmueble: Inmueble) -> Inmueble | None: ...

    @abstractmethod
    def delete(self, inmueble_id: int) -> bool: ...

    @abstractmethod
    def add_photo(self, inmueble_id: int, image_file, order: int = 0) -> InmueblePhoto | None:
        """Crea una foto asociada a un inmueble. Devuelve None si el inmueble no existe."""
        ...

    @abstractmethod
    def delete_photo(self, photo_id: int) -> bool:
        """Elimina una foto (y su archivo) por su id. Devuelve True si existía."""
        ...