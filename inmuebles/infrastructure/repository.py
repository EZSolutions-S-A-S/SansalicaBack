from django.core.paginator import Paginator
from django.db.models import Q

from inmuebles.domain.entities import Inmueble, InmueblePhoto
from inmuebles.domain.repositories import InmuebleFilters, InmuebleRepository

from .models import InmuebleModel, InmueblePhotoModel

VALID_ORDERING_FIELDS = {'price', '-price', 'square_meters', '-square_meters', 'created_at', '-created_at'}


class DjangoInmuebleRepository(InmuebleRepository):
    def __init__(self, request=None):
        self.request = request

    def _photo_url(self, photo: InmueblePhotoModel) -> str | None:
        if not photo.image:
            return None
        if self.request:
            return self.request.build_absolute_uri(photo.image.url)
        return photo.image.url

    def _to_entity(self, obj: InmuebleModel) -> Inmueble:
        return Inmueble(
            id=obj.id,
            title=obj.title,
            operation_type=obj.operation_type,
            property_type=obj.property_type,
            price=obj.price,
            square_meters=obj.square_meters,
            floor=obj.floor,
            bedrooms=obj.bedrooms,
            bathrooms=obj.bathrooms,
            parking_spots=obj.parking_spots,
            features=obj.features,
            amenities=obj.amenities,
            location=obj.location,
            description=obj.description,
            photos=[
                InmueblePhoto(id=photo.id, url=self._photo_url(photo), order=photo.order)
                for photo in obj.photos.all()
            ],
            status=obj.status,
            featured=obj.featured,
            created_at=obj.created_at,
        )

    def _apply_filters(self, queryset, filters: InmuebleFilters):
        if filters.operation_type:
            queryset = queryset.filter(operation_type=filters.operation_type)
        if filters.property_type:
            queryset = queryset.filter(property_type=filters.property_type)
        if filters.status:
            queryset = queryset.filter(status=filters.status)
        if filters.featured is not None:
            queryset = queryset.filter(featured=filters.featured)
        if filters.min_price is not None:
            queryset = queryset.filter(price__gte=filters.min_price)
        if filters.max_price is not None:
            queryset = queryset.filter(price__lte=filters.max_price)
        if filters.search:
            queryset = queryset.filter(
                Q(title__icontains=filters.search)
                | Q(location__icontains=filters.search)
                | Q(description__icontains=filters.search)
            )
        if filters.ordering and filters.ordering in VALID_ORDERING_FIELDS:
            queryset = queryset.order_by(filters.ordering)
        return queryset

    @staticmethod
    def _to_model_fields(inmueble: Inmueble) -> dict:
        return {
            'title': inmueble.title,
            'operation_type': inmueble.operation_type,
            'property_type': inmueble.property_type,
            'price': inmueble.price,
            'square_meters': inmueble.square_meters,
            'floor': inmueble.floor,
            'bedrooms': inmueble.bedrooms,
            'bathrooms': inmueble.bathrooms,
            'parking_spots': inmueble.parking_spots,
            'features': inmueble.features,
            'amenities': inmueble.amenities,
            'location': inmueble.location,
            'description': inmueble.description,
            'status': inmueble.status,
            'featured': inmueble.featured,
        }

    def list(self, filters: InmuebleFilters, page: int, page_size: int) -> tuple[list[Inmueble], int]:
        queryset = InmuebleModel.objects.prefetch_related('photos').all()
        queryset = self._apply_filters(queryset, filters)
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        return [self._to_entity(obj) for obj in page_obj.object_list], paginator.count

    def get(self, inmueble_id: int) -> Inmueble | None:
        obj = InmuebleModel.objects.prefetch_related('photos').filter(id=inmueble_id).first()
        return self._to_entity(obj) if obj else None

    def create(self, inmueble: Inmueble) -> Inmueble:
        obj = InmuebleModel.objects.create(**self._to_model_fields(inmueble))
        return self._to_entity(obj)

    def update(self, inmueble_id: int, inmueble: Inmueble) -> Inmueble | None:
        InmuebleModel.objects.filter(id=inmueble_id).update(**self._to_model_fields(inmueble))
        obj = InmuebleModel.objects.prefetch_related('photos').filter(id=inmueble_id).first()
        return self._to_entity(obj) if obj else None

    def delete(self, inmueble_id: int) -> bool:
        deleted, _ = InmuebleModel.objects.filter(id=inmueble_id).delete()
        return deleted > 0

    def add_photo(self, inmueble_id: int, image_file, order: int = 0) -> InmueblePhoto | None:
        if not InmuebleModel.objects.filter(id=inmueble_id).exists():
            return None

        photo = InmueblePhotoModel.objects.create(inmueble_id=inmueble_id, image=image_file, order=order)
        return InmueblePhoto(id=photo.id, url=self._photo_url(photo), order=photo.order)

    def delete_photo(self, photo_id: int) -> bool:
        photo = InmueblePhotoModel.objects.filter(id=photo_id).first()
        if not photo:
            return False

        photo.image.delete(save=False)
        photo.delete()
        return True