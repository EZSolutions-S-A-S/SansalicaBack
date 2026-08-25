import django.db.models.deletion
import inmuebles.infrastructure.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='InmuebleModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('operation_type', models.CharField(
                    choices=[('Venta', 'Venta'), ('Alquiler', 'Alquiler')],
                    max_length=20,
                )),
                ('property_type', models.CharField(
                    choices=[
                        ('Casa', 'Casa'),
                        ('Apartamento', 'Apartamento'),
                        ('Local Comercial', 'Local Comercial'),
                        ('Terreno', 'Terreno'),
                    ],
                    max_length=30,
                )),
                ('price', models.DecimalField(decimal_places=2, max_digits=14)),
                ('location', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('square_meters', models.DecimalField(decimal_places=2, max_digits=10)),
                ('floor', models.IntegerField(blank=True, null=True)),
                ('bedrooms', models.IntegerField(blank=True, null=True)),
                ('bathrooms', models.IntegerField(blank=True, null=True)),
                ('parking_spots', models.IntegerField(blank=True, null=True)),
                ('features', models.JSONField(blank=True, default=list)),
                ('amenities', models.JSONField(blank=True, default=list)),
                ('status', models.CharField(
                    choices=[
                        ('Disponible', 'Disponible'),
                        ('Reservado', 'Reservado'),
                        ('Vendido', 'Vendido'),
                    ],
                    default='Disponible',
                    max_length=20,
                )),
                ('featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'inmuebles_inmueble',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InmueblePhotoModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=inmuebles.infrastructure.models.inmueble_photo_path)),
                ('order', models.PositiveIntegerField(default=0)),
                ('inmueble', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='photos',
                    to='inmuebles.inmueblemodel',
                )),
            ],
            options={
                'db_table': 'inmuebles_inmueble_photo',
                'ordering': ['order', 'id'],
            },
        ),
    ]