from inmuebles.domain.entities import Inmueble
from inmuebles.domain.repositories import InmuebleFilters, InmuebleRepository


class ListInmuebles:
    def __init__(self, repository: InmuebleRepository):
        self.repository = repository

    def execute(self, filters: InmuebleFilters, page: int, page_size: int) -> tuple[list[Inmueble], int]:
        return self.repository.list(filters, page, page_size)


class GetInmueble:
    def __init__(self, repository: InmuebleRepository):
        self.repository = repository

    def execute(self, inmueble_id: int) -> Inmueble | None:
        return self.repository.get(inmueble_id)


class CreateInmueble:
    def __init__(self, repository: InmuebleRepository):
        self.repository = repository

    def execute(self, inmueble: Inmueble) -> Inmueble:
        return self.repository.create(inmueble)


class UpdateInmueble:
    def __init__(self, repository: InmuebleRepository):
        self.repository = repository

    def execute(self, inmueble_id: int, inmueble: Inmueble) -> Inmueble | None:
        return self.repository.update(inmueble_id, inmueble)


class DeleteInmueble:
    def __init__(self, repository: InmuebleRepository):
        self.repository = repository

    def execute(self, inmueble_id: int) -> bool:
        return self.repository.delete(inmueble_id)