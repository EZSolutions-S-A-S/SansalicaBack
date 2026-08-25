# Capa DOMAIN — reglas del negocio en su forma más pura.
#
# Reglas de esta capa:
#   - Solo Python puro: dataclasses, enum, datetime, decimal.
#   - JAMÁS importar Django, DRF, ni nada de application/infrastructure/api.
#   - Aquí se define QUÉ es un "Maquillaje", no CÓMO se guarda.

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class Categoria(str, Enum):
    """Categorías posibles de un producto de maquillaje."""
    LABIAL = 'Labial'
    BASE = 'Base'
    RUBOR = 'Rubor'
    SOMBRA = 'Sombra'
    MASCARA = 'Máscara de pestañas'


@dataclass
class Maquillaje:
    """Un producto del catálogo de maquillaje.

    Esta es la representación "pura" del maquillaje — no tiene nada que ver
    con cómo se guarda en la base de datos (eso vive en infrastructure/models.py).
    """
    nombre: str
    categoria: Categoria
    precio: Decimal
    marca: str
    id: int | None = None
    stock: int = 0
    descripcion: str = ''
    disponible: bool = True
