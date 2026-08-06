# Capa DOMAIN — el "contrato" que cualquier forma de guardar maquillajes debe cumplir.
#
# Esta interfaz (ABC = clase abstracta) no sabe si los datos se guardan en
# Postgres, SQLite, un archivo, o en memoria. Eso lo decide infrastructure/.
#
# application/ y api/ solo conocen ESTA interfaz, nunca la implementación real.

from abc import ABC, abstractmethod

from .entities import Maquillaje


class MaquillajeFilters:
    """Filtros opcionales para listar maquillajes (búsqueda, categoría, etc.)."""

    def __init__(self, categoria: str | None = None, disponible: bool | None = None, search: str | None = None):
        self.categoria = categoria
        self.disponible = disponible
        self.search = search


class MaquillajeRepository(ABC):
    """Contrato que debe cumplir cualquier implementación de persistencia."""

    @abstractmethod
    def list(self, filters: MaquillajeFilters, page: int, page_size: int) -> tuple[list[Maquillaje], int]:
        """Devuelve (resultados_de_la_página, total_de_resultados)."""
        raise NotImplementedError

    @abstractmethod
    def get(self, maquillaje_id: int) -> Maquillaje | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, maquillaje: Maquillaje) -> Maquillaje:
        raise NotImplementedError

    @abstractmethod
    def update(self, maquillaje_id: int, maquillaje: Maquillaje) -> Maquillaje | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, maquillaje_id: int) -> bool:
        raise NotImplementedError
