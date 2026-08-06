# Capa INFRASTRUCTURE — cómo se guardan los datos de verdad (Django ORM).
#
# Reglas de esta capa:
#   - Aquí SÍ se importa Django — es la única capa (junto con api/) que puede.
#   - Los campos deben reflejar los mismos datos que domain/entities.py,
#     pero esto es un detalle técnico de base de datos, no la regla de negocio.
#   - domain/ y application/ NUNCA deben importar este archivo directamente.

from django.db import models


class MaquillajeModel(models.Model):
    # Django necesita SU PROPIA clase de choices (no puede reusar directamente
    # el Enum de domain/entities.py, porque ese Enum es Python puro y no sabe
    # nada de bases de datos). Por eso existen dos "Categoria": una en domain/
    # (la regla de negocio: qué categorías existen) y esta de aquí (el detalle
    # técnico: cómo Django valida/guarda ese valor en la columna).
    class Categoria(models.TextChoices):
        LABIAL = 'Labial', 'Labial'
        BASE = 'Base', 'Base'
        RUBOR = 'Rubor', 'Rubor'
        SOMBRA = 'Sombra', 'Sombra'
        MASCARA = 'Máscara de pestañas', 'Máscara de pestañas'

    # Estos campos deben coincidir en significado con los de
    # domain/entities.py::Maquillaje — pero aquí SÍ importa el tipo de columna
    # (CharField, DecimalField, etc.), algo que a domain/ no le interesa.
    nombre = models.CharField(max_length=255)
    categoria = models.CharField(max_length=30, choices=Categoria.choices)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    marca = models.CharField(max_length=100)
    stock = models.PositiveIntegerField(default=0)
    descripcion = models.TextField(blank=True)
    disponible = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)  # se llena sola al crear, nadie la escribe a mano

    class Meta:
        # app_label le dice a Django "este modelo pertenece a la app maquillaje",
        # aunque el archivo físico viva dentro de infrastructure/ y no en la
        # raíz del app (que es donde Django buscaría por convención).
        app_label = 'maquillaje'
        # Nombre real de la tabla en la base de datos. Sin esto, Django usaría
        # un nombre automático (ej. "maquillaje_maquillajemodel") — lo dejamos
        # explícito para que sea predecible si alguna vez hay que mirar la BD
        # directamente (psql, DBeaver, etc.).
        db_table = 'maquillaje_maquillaje'
        ordering = ['-creado_en']  # por defecto, lo más reciente primero

    def __str__(self):
        return self.nombre
