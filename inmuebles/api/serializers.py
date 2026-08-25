from rest_framework import serializers

from ..domain.entities import Inmueble, InmueblePhoto, OperationType, PropertyType, Status

class InmueblePhotoSerializer(serializers.Serializer):
    url = serializers.CharField(allow_null=True, required=False)
    order = serializers.IntegerField(required=False, default=0)

class InmuebleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)


    title = serializers.CharField(max_length=255)
    operation_type = serializers.ChoiceField(choices=[e.value for e in OperationType])
    property_type = serializers.ChoiceField(choices=[e.value for e in PropertyType])
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    square_meters = serializers.DecimalField(max_digits=10, decimal_places=2)
    location = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)

    floor = serializers.IntegerField(required=False, allow_null=True)
    bedrooms = serializers.IntegerField(required=False, allow_null=True)
    bathrooms = serializers.IntegerField(required=False, allow_null=True)
    parking_spots = serializers.IntegerField(required=False, allow_null=True)

    features = serializers.ListField(child=serializers.CharField(), required=False)
    amenities = serializers.ListField(child=serializers.CharField(), required=False)
    photos = InmueblePhotoSerializer(many=True, required=False)

    status = serializers.ChoiceField(choices=[e.value for e in Status], required=False)
    featured = serializers.BooleanField(required=False)
    created_at = serializers.DateTimeField(read_only=True, required=False)

    def create(self, validated_data):
        return self._to_entity(validated_data)

    def update(self, instance, validated_data):
        updated = self._to_entity(validated_data)
        updated.id = instance.id
        return updated

    def _to_entity(self, data: dict) -> Inmueble:
        photos_data = data.get('photos', [])
        photos = [InmueblePhoto(url=p.get('url'), order=p.get('order', 0)) for p in photos_data]

        return Inmueble(
            id=data.get('id'),
            title=data['title'],
            operation_type=OperationType(data['operation_type']),
            property_type=PropertyType(data['property_type']),
            price=data['price'],
            square_meters=data['square_meters'],
            location=data['location'],
            description=data.get('description', ''),
            floor=data.get('floor'),
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            parking_spots=data.get('parking_spots'),
            features=data.get('features', []),
            amenities=data.get('amenities', []),
            photos=photos,
            status=Status(data['status']) if data.get('status') else Status.DISPONIBLE,
            featured=data.get('featured', False),
        )