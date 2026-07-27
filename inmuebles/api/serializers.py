from rest_framework import serializers

from inmuebles.domain.entities import (
    Inmueble,
    InmueblePhoto,
    OperationType,
    PropertyType,
    Status,
)


class InmueblePhotoSerializer(serializers.Serializer):
    url = serializers.CharField()
    order = serializers.IntegerField()


class InmuebleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=255)
    operation_type = serializers.ChoiceField(choices=[e.value for e in OperationType])
    property_type = serializers.ChoiceField(choices=[e.value for e in PropertyType])
    price = serializers.DecimalField(max_digits=14, decimal_places=2)
    square_meters = serializers.DecimalField(max_digits=10, decimal_places=2)
    floor = serializers.IntegerField(required=False, allow_null=True)
    bedrooms = serializers.IntegerField(required=False, allow_null=True)
    bathrooms = serializers.IntegerField(required=False, allow_null=True)
    parking_spots = serializers.IntegerField(required=False, allow_null=True)
    features = serializers.ListField(child=serializers.CharField(), required=False)
    amenities = serializers.ListField(child=serializers.CharField(), required=False)
    location = serializers.CharField(max_length=255)
    description = serializers.CharField()
    photos = InmueblePhotoSerializer(many=True, read_only=True)
    status = serializers.ChoiceField(choices=[e.value for e in Status], required=False)
    featured = serializers.BooleanField(required=False)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data) -> Inmueble:
        return Inmueble(**validated_data)

    def update(self, instance: Inmueble, validated_data) -> Inmueble:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance
