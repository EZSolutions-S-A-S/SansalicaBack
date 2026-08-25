# Capa API — SERIALIZER: el traductor JSON ↔ Python.
#
# Cuando llega una request, el body viaja como JSON (texto plano). Cuando
# respondes, también tiene que ser JSON. El serializer traduce en ambas
# direcciones:
#   - Entrada: recibe JSON crudo, valida tipos/campos requeridos (ej. "precio"
#     debe ser un decimal válido, "nombre" no puede faltar) y, si pasa la
#     validación, lo convierte en un objeto Python (un Maquillaje).
#   - Salida: toma un Maquillaje y lo convierte en un diccionario que Django
#     puede transformar a JSON en la respuesta.
#
# Nota: es un serializers.Serializer normal, NO un ModelSerializer — así se
# mantiene desacoplado del modelo de Django, y solo conoce el dataclass Maquillaje.
# Si fuera ModelSerializer, quedaría atado directamente al ORM y rompería la
# separación de capas (api/ nunca debe saber cómo se guardan los datos).

from rest_framework import serializers

from ..domain.entities import Maquillaje




class MaquillajeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(max_length=255)
    categoria = serializers.CharField()
    precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    marca = serializers.CharField(max_length=100)
    stock = serializers.IntegerField(required=False)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    disponible = serializers.BooleanField(required=False)

    def create(self, validated_data):
        return Maquillaje(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance
