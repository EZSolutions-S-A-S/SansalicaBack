from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..serializers import InmuebleSerializer, InmueblePhotoSerializer
from ...application.photo_use_cases import AddInmueblePhoto, DeleteInmueblePhoto
from ...application.use_cases import (
    CreateInmueble,
    DeleteInmueble,
    GetInmueble,
    ListInmuebles,
    UpdateInmueble,
)
from ...composition import get_inmueble_repository
from ...domain.repositories import InmuebleFilters

from .permissions import IsStaffUser
from .serializers import InmueblePhotoUploadSerializer

ORDERING_FIELDS = {'price', '-price', 'square_meters', '-square_meters', 'created_at', '-created_at'}


class AdminInmuebleViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsStaffUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _repository(self):
        return get_inmueble_repository(request=self.request)

    def _filters_from_query_params(self, params) -> InmuebleFilters:
        featured = params.get('featured')
        ordering = params.get('ordering')

        return InmuebleFilters(
            operation_type=params.get('operation_type'),
            property_type=params.get('property_type'),
            status=params.get('status'),
            featured=(featured.lower() == 'true') if featured is not None else None,
            min_price=params.get('min_price'),
            max_price=params.get('max_price'),
            search=params.get('search'),
            ordering=ordering if ordering in ORDERING_FIELDS else None,
        )

    def list(self, request):
        filters = self._filters_from_query_params(request.query_params)
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        results, total = ListInmuebles(self._repository()).execute(filters, page, page_size)
        serializer = InmuebleSerializer(results, many=True)

        return Response({'count': total, 'page': page, 'page_size': page_size, 'results': serializer.data})

    def retrieve(self, request, pk=None):
        inmueble = GetInmueble(self._repository()).execute(int(pk))
        if not inmueble:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(InmuebleSerializer(inmueble).data)

    def create(self, request):
        serializer = InmuebleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created = CreateInmueble(self._repository()).execute(serializer.save())
        return Response(InmuebleSerializer(created).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        existing = GetInmueble(self._repository()).execute(int(pk))
        if not existing:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = InmuebleSerializer(existing, data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = UpdateInmueble(self._repository()).execute(int(pk), serializer.save())
        return Response(InmuebleSerializer(updated).data)

    def partial_update(self, request, pk=None):
        existing = GetInmueble(self._repository()).execute(int(pk))
        if not existing:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = InmuebleSerializer(existing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = UpdateInmueble(self._repository()).execute(int(pk), serializer.save())
        return Response(InmuebleSerializer(updated).data)

    def destroy(self, request, pk=None):
        deleted = DeleteInmueble(self._repository()).execute(int(pk))
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='photos')
    def upload_photo(self, request, pk=None):
        inmueble = GetInmueble(self._repository()).execute(int(pk))
        if not inmueble:
            return Response(status=status.HTTP_404_NOT_FOUND)

        upload_serializer = InmueblePhotoUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        photo = AddInmueblePhoto(self._repository()).execute(
            inmueble_id=int(pk),
            image_file=upload_serializer.validated_data['image'],
            order=upload_serializer.validated_data.get('order', 0),
        )
        return Response(InmueblePhotoSerializer(photo).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'photos/(?P<photo_id>\d+)')
    def delete_photo(self, request, pk=None, photo_id=None):
        deleted = DeleteInmueblePhoto(self._repository()).execute(int(photo_id))
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
