from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class StaffTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_staff:
            raise AuthenticationFailed('Solo usuarios staff pueden acceder al panel de administración.')
        return data


class InmueblePhotoUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    order = serializers.IntegerField(required=False, default=0)
