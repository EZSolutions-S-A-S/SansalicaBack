# Shim requerido por convención de Django (busca "models.py" en la raíz del
# app). La implementación real vive en infrastructure/models.py — este
# archivo solo re-exporta, igual que inmuebles/models.py en el proyecto real.
from .infrastructure.models import MaquillajeModel

__all__ = ['MaquillajeModel']
