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
    square_meters = models.DecimalField(max_digits=10, decimal_places=2)
    floor = models.IntegerField(null=True, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    parking_spots = models.IntegerField(null=True, blank=True)
    features = models.JSONField(default=list, blank=True)
    amenities = models.JSONField(default=list, blank=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DISPONIBLE)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'inmuebles'
        db_table = 'inmuebles_inmueble'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class InmueblePhotoModel(models.Model):
    inmueble = models.ForeignKey(InmuebleModel, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=inmueble_photo_path)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = 'inmuebles'
        db_table = 'inmuebles_inmueble_photo'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.inmueble.title} - foto {self.order}'
