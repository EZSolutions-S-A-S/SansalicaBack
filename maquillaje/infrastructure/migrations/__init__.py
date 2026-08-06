# Capa INFRASTRUCTURE — MIGRATIONS: el historial versionado del esquema de
# la base de datos.
#
# Cada archivo de esta carpeta (ej. 0001_initial.py) describe UN cambio
# concreto al esquema: "crear esta tabla", "agregar esta columna", etc.
#
#   - `python manage.py makemigrations maquillaje` compara los modelos
#     actuales (infrastructure/models.py) contra el último estado conocido
#     y genera el archivo de migración nuevo si hay diferencias.
#   - `python manage.py migrate` es quien de verdad EJECUTA esos cambios
#     contra la base de datos real (crea/altera las tablas).
#
# Los archivos de migración se generan automáticamente — no se editan a
# mano (salvo casos avanzados que no aplican aquí).
#
# Nota de ubicación: estas migraciones viven dentro de infrastructure/ (no
# en maquillaje/migrations/, que es donde Django las buscaría por defecto)
# porque MIGRATION_MODULES en sansalica_backend/settings.py las redirige
# aquí — es 100% un detalle de infraestructura/ORM, coherente con la regla
# de la capa (ver ARCHITECTURE.md, sección 2).
