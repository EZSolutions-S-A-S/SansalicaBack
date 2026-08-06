# Capa API — VIEW (en DRF, "ViewSet"): la puerta de entrada HTTP.
#
# Aquí se juntan: autenticación, permisos, serializers y casos de uso — pero
# la lógica de negocio NUNCA vive aquí. El "View"/"ViewSet" solo orquesta:
# recibe el request, llama al caso de uso correcto, y devuelve una Response
# con el código de estado adecuado (200, 201, 404, etc.).
#
# ¿Qué es un "Controller" y por qué esto no se llama así?
# Si vienes de Laravel, Rails o Spring, esto es exactamente lo que ahí
# llamarían "Controller": el componente que recibe la petición HTTP y decide
# qué hacer con ella. Es el MISMO concepto, solo que Django usa otro nombre
# por su propia convención histórica — Django describe su arquitectura como
# "MTV" (Model-Template-View) en vez de "MVC":
#     MVC:  Controller  →  View (el HTML final)   →  Model
#     MTV:  View         →  Template (el HTML final) →  Model
# O sea, lo que en MVC es el "Controller", en Django/DRF se llama "View".
# No falta el concepto de Controller — está aquí, solo que con otro nombre.
# Por eso este archivo (y la clase de abajo) se llaman "views", no
# "controllers": es el término que usa Django/DRF y el que vas a encontrar
# en su documentación oficial y en cualquier tutorial o respuesta en
# Stack Overflow sobre este framework.
#
# Fíjate que el import de abajo es de "composition", no de "infrastructure.repository".
# Ese es el detalle que hace que esta capa esté desacoplada (ver ARCHITECTURE.md).

from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from ..application.use_cases import (
    ActualizarMaquillaje,
    CrearMaquillaje,
    EliminarMaquillaje,
    GetMaquillaje,
    ListMaquillajes,
)
from ..composition import get_maquillaje_repository
from ..domain.repositories import MaquillajeFilters
from .serializers import MaquillajeSerializer


class MaquillajeViewSet(viewsets.ViewSet):
    # Ejemplo sin autenticación custom (a diferencia de inmuebles/) para
    # mantener el foco en la arquitectura, no en auth. En un caso real,
    # aquí irían authentication_classes/permission_classes específicos.
    permission_classes = [permissions.AllowAny]

    def _repository(self):
        return get_maquillaje_repository(request=self.request)

    def _filters_from_query_params(self, params) -> MaquillajeFilters:
        disponible = params.get('disponible')
        return MaquillajeFilters(
            categoria=params.get('categoria'),
            disponible=(disponible.lower() == 'true') if disponible is not None else None,
            search=params.get('search'),
        )

    def list(self, request):
        filters = self._filters_from_query_params(request.query_params)
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        results, total = ListMaquillajes(self._repository()).execute(filters, page, page_size)
        serializer = MaquillajeSerializer(results, many=True)

        return Response({'count': total, 'page': page, 'page_size': page_size, 'results': serializer.data})

    def retrieve(self, request, pk=None):
        maquillaje = GetMaquillaje(self._repository()).execute(int(pk))
        if not maquillaje:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(MaquillajeSerializer(maquillaje).data)

    def create(self, request):
        serializer = MaquillajeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created = CrearMaquillaje(self._repository()).execute(serializer.save())
        return Response(MaquillajeSerializer(created).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        existing = GetMaquillaje(self._repository()).execute(int(pk))
        if not existing:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = MaquillajeSerializer(existing, data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = ActualizarMaquillaje(self._repository()).execute(int(pk), serializer.save())
        return Response(MaquillajeSerializer(updated).data)

    def partial_update(self, request, pk=None):
        existing = GetMaquillaje(self._repository()).execute(int(pk))
        if not existing:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = MaquillajeSerializer(existing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = ActualizarMaquillaje(self._repository()).execute(int(pk), serializer.save())
        return Response(MaquillajeSerializer(updated).data)

    def destroy(self, request, pk=None):
        deleted = EliminarMaquillaje(self._repository()).execute(int(pk))
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
