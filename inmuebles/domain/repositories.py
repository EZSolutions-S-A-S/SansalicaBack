from abc import ABC, abstractmethod

from .entities import Inmueble


class InmuebleFilters:
    def __init__(
        self,
        operation_type: str | None = None,
        property_type: str | None = None,
        status: str | None = None,
        featured: bool | None = None,
        min_price=None,
        max_price=None,
        search: str | None = None,
        ordering: str | None = None,
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
    """Contrato que debe cumplir cualquier implementación de persistencia."""

    @abstractmethod
    def list(self, filters: InmuebleFilters, page: int, page_size: int) -> tuple[list[Inmueble], int]:
        """Devuelve (resultados_de_la_página, total_de_resultados)."""
        raise NotImplementedError

    @abstractmethod
    def get(self, inmueble_id: int) -> Inmueble | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, inmueble: Inmueble) -> Inmueble:
        raise NotImplementedError

    @abstractmethod
    def update(self, inmueble_id: int, inmueble: Inmueble) -> Inmueble | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, inmueble_id: int) -> bool:
        raise NotImplementedError
