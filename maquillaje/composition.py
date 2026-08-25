# Punto ÚNICO de conexión entre la interfaz (domain) y la implementación real
# (infrastructure). Este es el ÚNICO archivo que debería conocer el nombre de
# la clase concreta — ni siquiera api/views.py debería importarla directamente.
#
# Ver ARCHITECTURE.md, sección 3, para la explicación completa de por qué
# existe este archivo.

from django.conf import settings
from django.utils.module_loading import import_string

from .domain.repositories import MaquillajeRepository


def get_maquillaje_repository(request=None) -> MaquillajeRepository:
    repository_class = import_string(settings.MAQUILLAJE_REPOSITORY_CLASS)
    return repository_class()
