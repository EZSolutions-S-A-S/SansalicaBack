from django.conf import settings
from django.db import models


def inmueble_photo_path(instance, filename):
    return f'inmuebles/{instance.inmueble_id}/{filename}'


class InmuebleModel(models.Model):
    class OperationType(models.TextChoices):
        VENTA = 'Venta', 'Venta'
        ALQUILER = 'Alquiler', 'Alquiler'

    class PropertyType(models.TextChoices):
        CASA = 'Casa', 'Casa'
        APARTAMENTO = 'Apartamento', 'Apartamento'
        LOCAL_COMERCIAL = 'Local Comercial', 'Local Comercial'
        TERRENO = 'Terreno', 'Terreno'

    class Status(models.TextChoices):
        DISPONIBLE = 'Disponible', 'Disponible'
        RESERVADO = 'Reservado', 'Reservado'
        VENDIDO = 'Vendido', 'Vendido'

    title = models.CharField(max_length=255)
    operation_type = models.CharField(max_length=20, choices=OperationType.choices)
    property_type = models.CharField(max_length=30, choices=PropertyType.choices)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    location = models.CharField(max_length=255)
    description = models.TextField()
    square_meters = models.DecimalField(max_digits=10, decimal_places=2)
    floor = models.IntegerField(null=True, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    parking_spots = models.IntegerField(null=True, blank=True)
    features = models.JSONField(default=list, blank=True)
    amenities = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DISPONIBLE)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'inmuebles'
        db_table = 'inmuebles_inmueble'
        ordering = ['-created_at']


class InmueblePhotoModel(models.Model):
    inmueble = models.ForeignKey(InmuebleModel, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to=inmueble_photo_path)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = 'inmuebles'
        db_table = 'inmuebles_inmueble_photo'
        ordering = ['order', 'id']


class AdminProfileModel(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='admin_profiles/', null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        app_label = 'inmuebles'
        db_table = 'inmuebles_admin_profile'