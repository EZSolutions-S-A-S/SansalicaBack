# Capa APPLICATION — casos de uso: qué pasa cuando alguien quiere listar,
# obtener, crear, actualizar o borrar un maquillaje. Cada clase es una sola
# operación, orquestando el repositorio — sin lógica de negocio compleja.

from ..domain.entities import Maquillaje
from ..domain.repositories import MaquillajeFilters, MaquillajeRepository


class ListMaquillajes:
    """Caso de uso: listar maquillajes con filtros y paginación."""

    def __init__(self, repository: MaquillajeRepository):
        self.repository = repository

    def execute(self, filters: MaquillajeFilters, page: int, page_size: int) -> tuple[list[Maquillaje], int]:
        return self.repository.list(filters, page, page_size)


class GetMaquillaje:
    """Caso de uso: obtener un maquillaje por su id."""

    def __init__(self, repository: MaquillajeRepository):
        self.repository = repository

    def execute(self, maquillaje_id: int) -> Maquillaje | None:
        return self.repository.get(maquillaje_id)


class CrearMaquillaje:
    """Caso de uso: crear un maquillaje nuevo."""

    def __init__(self, repository: MaquillajeRepository):
        self.repository = repository

    def execute(self, maquillaje: Maquillaje) -> Maquillaje:
        return self.repository.create(maquillaje)


class ActualizarMaquillaje:
    """Caso de uso: actualizar un maquillaje existente."""

    def __init__(self, repository: MaquillajeRepository):
        self.repository = repository

    def execute(self, maquillaje_id: int, maquillaje: Maquillaje) -> Maquillaje | None:
        return self.repository.update(maquillaje_id, maquillaje)


class EliminarMaquillaje:
    """Caso de uso: eliminar un maquillaje por su id."""

    def __init__(self, repository: MaquillajeRepository):
        self.repository = repository

    def execute(self, maquillaje_id: int) -> bool:
        return self.repository.delete(maquillaje_id)
