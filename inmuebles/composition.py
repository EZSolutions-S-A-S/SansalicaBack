from django.conf import settings
from django.utils.module_loading import import_string

from .domain.repositories import InmuebleRepository


def get_inmueble_repository(request=None) -> InmuebleRepository:
    repository_class = import_string(settings.INMUEBLE_REPOSITORY_CLASS)
    return repository_class(request=request)