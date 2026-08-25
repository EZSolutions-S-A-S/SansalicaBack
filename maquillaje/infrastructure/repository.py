# Capa INFRASTRUCTURE — la implementación REAL de la interfaz definida en domain/.
#
# Esta clase es la única que sabe traducir entre "Maquillaje" (dataclass puro)
# y "MaquillajeModel" (fila de base de datos). Nadie más en el proyecto debería
# hacer esa traducción.

from django.core.paginator import Paginator
from django.db.models import Q

from ..domain.entities import Maquillaje
from ..domain.repositories import MaquillajeFilters, MaquillajeRepository
from .models import MaquillajeModel


# "implementa" MaquillajeRepository: hereda de esa clase abstracta y le da
# cuerpo real a cada método. Esta es la clase que composition.py resuelve
# dinámicamente (ver composition.py) — nadie más en el proyecto la importa
# directamente por su nombre.
class MaquillajeRepositoryImpl(MaquillajeRepository):
    # Convierte una fila de la base de datos (MaquillajeModel) en un objeto
    # de dominio puro (Maquillaje). Todo lo que sale de este repositorio hacia
    # application/api/ ya viene en forma de Maquillaje, nunca de MaquillajeModel
    # — así esas capas nunca necesitan saber que existe Django.
    def _to_entity(self, obj: MaquillajeModel) -> Maquillaje:
        return Maquillaje(
            id=obj.id,
            nombre=obj.nombre,
            categoria=obj.categoria,
            precio=obj.precio,
            marca=obj.marca,
            stock=obj.stock,
            descripcion=obj.descripcion,
            disponible=obj.disponible,
        )

    # Traduce el MaquillajeFilters (un objeto plano, sin Django) a llamadas
    # reales de QuerySet.filter(...). MaquillajeFilters no sabe qué es un
    # QuerySet — esa traducción vive únicamente aquí.
    def _apply_filters(self, queryset, filters: MaquillajeFilters):
        if filters.categoria:
            queryset = queryset.filter(categoria=filters.categoria)
        if filters.disponible is not None:
            queryset = queryset.filter(disponible=filters.disponible)
        if filters.search:
            queryset = queryset.filter(Q(nombre__icontains=filters.search) | Q(marca__icontains=filters.search))
        return queryset

    # Cada método de abajo sigue el mismo patrón: 1) hablar con el ORM
    # (MaquillajeModel.objects...), 2) convertir el resultado con _to_entity
    # antes de devolverlo. Así el "contrato" de MaquillajeRepository (ver
    # domain/repositories.py) se cumple exactamente.
    def list(self, filters: MaquillajeFilters, page: int, page_size: int) -> tuple[list[Maquillaje], int]:
        queryset = MaquillajeModel.objects.all()
        queryset = self._apply_filters(queryset, filters)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        return [self._to_entity(obj) for obj in page_obj.object_list], paginator.count

    def get(self, maquillaje_id: int) -> Maquillaje | None:
        obj = MaquillajeModel.objects.filter(id=maquillaje_id).first()
        return self._to_entity(obj) if obj else None

    def create(self, maquillaje: Maquillaje) -> Maquillaje:
        obj = MaquillajeModel.objects.create(**self._to_model_fields(maquillaje))
        return self._to_entity(obj)

    def update(self, maquillaje_id: int, maquillaje: Maquillaje) -> Maquillaje | None:
        MaquillajeModel.objects.filter(id=maquillaje_id).update(**self._to_model_fields(maquillaje))
        obj = MaquillajeModel.objects.filter(id=maquillaje_id).first()
        return self._to_entity(obj) if obj else None

    def delete(self, maquillaje_id: int) -> bool:
        deleted, _ = MaquillajeModel.objects.filter(id=maquillaje_id).delete()
        return deleted > 0

    # El viaje inverso a _to_entity: toma un Maquillaje (dominio) y lo
    # convierte en un diccionario de kwargs que el ORM entiende, para poder
    # usarlo en .create(**campos) o .update(**campos).
    @staticmethod
    def _to_model_fields(maquillaje: Maquillaje) -> dict:
        return {
            'nombre': maquillaje.nombre,
            'categoria': maquillaje.categoria,
            'precio': maquillaje.precio,
            'marca': maquillaje.marca,
            'stock': maquillaje.stock,
            'descripcion': maquillaje.descripcion,
            'disponible': maquillaje.disponible,
        }
