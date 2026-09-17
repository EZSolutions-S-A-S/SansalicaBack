from decimal import Decimal, InvalidOperation

from rest_framework import status, viewsets
from rest_framework.response import Response

from ..application.use_cases import GetInmueble, ListInmuebles
from ..composition import get_inmueble_repository
from ..domain.repositories import InmuebleFilters
from .authentication import ReadOnlyApiKeyAuthentication
from .errors import InvalidPageError, InvalidPageSizeError, InvalidPriceRangeError, InvalidRoomsFilterError
from .permissions import HasApiKey
from .serializers import InmuebleSerializer


class InmuebleViewSet(viewsets.ViewSet):
    authentication_classes = [ReadOnlyApiKeyAuthentication]
    permission_classes = [HasApiKey]

    def _repository(self):
        return get_inmueble_repository(request=self.request)

    def _filters_from_query_params(self, params) -> InmuebleFilters:
        featured = params.get('featured')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        min_bedrooms = params.get('min_bedrooms')
        min_bathrooms = params.get('min_bathrooms')
        min_parking_spots = params.get('min_parking_spots')

        try:
            min_price = Decimal(min_price) if min_price else None
            max_price = Decimal(max_price) if max_price else None
        except InvalidOperation:
            raise InvalidPriceRangeError()

        try:
            min_bedrooms = int(min_bedrooms) if min_bedrooms else None
            min_bathrooms = int(min_bathrooms) if min_bathrooms else None
            min_parking_spots = int(min_parking_spots) if min_parking_spots else None
        except ValueError:
            raise InvalidRoomsFilterError()

        return InmuebleFilters(
            operation_type=params.get('operation_type'),
            property_type=params.get('property_type'),
            status=params.get('status'),
            featured=(featured.lower() == 'true') if featured is not None else None,
            min_price=min_price,
            max_price=max_price,
            search=params.get('search'),
            ordering=params.get('ordering'),
            departamento=params.get('departamento'),
            ciudad=params.get('ciudad'),
            min_bedrooms=min_bedrooms,
            min_bathrooms=min_bathrooms,
            min_parking_spots=min_parking_spots,
            # Casillas repetidas del mismo filtro (?features=Balcón&features=Terraza):
            # coinciden los inmuebles que tengan TODOS los valores pedidos (AND), no
            # basta con tener alguno.
            features=params.getlist('features') or None,
            amenities=params.getlist('amenities') or None,
        )

    def list(self, request):
        try:
            page = int(request.query_params.get('page', 1))
        except ValueError:
            raise InvalidPageError()

        try:
            page_size = int(request.query_params.get('page_size', 20))
        except ValueError:
            raise InvalidPageSizeError()

        filters = self._filters_from_query_params(request.query_params)

        results, total = ListInmuebles(self._repository()).execute(filters, page, page_size)
        serializer = InmuebleSerializer(results, many=True)

        return Response({'count': total, 'page': page, 'page_size': page_size, 'results': serializer.data})

    def retrieve(self, request, pk=None):
        inmueble = GetInmueble(self._repository()).execute(int(pk))
        if not inmueble:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(InmuebleSerializer(inmueble).data)