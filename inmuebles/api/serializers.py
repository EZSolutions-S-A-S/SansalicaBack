from rest_framework import serializers

from ..domain.entities import Inmueble, OperationType, PropertyType, Status
from .errors import MustBeNonNegative, MustBePositive

class InmueblePhotoSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.CharField(allow_null=True, required=False)
    order = serializers.IntegerField(required=False, default=0)

class InmuebleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)


    title = serializers.CharField(max_length=255)
    operation_type = serializers.ChoiceField(choices=[e.value for e in OperationType])
    property_type = serializers.ChoiceField(choices=[e.value for e in PropertyType])
    price = serializers.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MustBePositive('Price must be greater than 0.')],
    )
    square_meters = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MustBePositive('Square meters must be greater than 0.')],
    )
    location = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True)

    # floor no lleva validador de rango a propósito: un piso de sótano (-1, -2)
    # es un valor legítimo, así que sí se permiten negativos aquí.
    floor = serializers.IntegerField(required=False, allow_null=True)
    bedrooms = serializers.IntegerField(
        required=False, allow_null=True,
        validators=[MustBeNonNegative('Bedrooms cannot be negative.')],
    )
    bathrooms = serializers.IntegerField(
        required=False, allow_null=True,
        validators=[MustBeNonNegative('Bathrooms cannot be negative.')],
    )
    parking_spots = serializers.IntegerField(
        required=False, allow_null=True,
        validators=[MustBeNonNegative('Parking spots cannot be negative.')],
    )

    features = serializers.ListField(child=serializers.CharField(), required=False)
    amenities = serializers.ListField(child=serializers.CharField(), required=False)
    # Las fotos son de solo lectura aquí: se gestionan por endpoints dedicados
    # (subir/borrar una foto), nunca a través del payload de crear/editar el
    # inmueble. Así se evita aceptar un campo que después no se persiste.
    photos = InmueblePhotoSerializer(many=True, read_only=True)

    status = serializers.ChoiceField(choices=[e.value for e in Status], required=False)
    featured = serializers.BooleanField(required=False)
    created_at = serializers.DateTimeField(read_only=True, required=False)

    def create(self, validated_data):
        return self._to_entity(validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'operation_type':
                value = OperationType(value)
            elif attr == 'property_type':
                value = PropertyType(value)
            elif attr == 'status':
                value = Status(value)
            setattr(instance, attr, value)
        return instance

    def _to_entity(self, data: dict) -> Inmueble:
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
            status=Status(data['status']) if data.get('status') else Status.DISPONIBLE,
            featured=data.get('featured', False),
        )
