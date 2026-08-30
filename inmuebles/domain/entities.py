from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OperationType(str, Enum):
    VENTA = 'Venta'
    ALQUILER = 'Alquiler'


class PropertyType(str, Enum):
    CASA = 'Casa'
    APARTAMENTO = 'Apartamento'
    LOCAL_COMERCIAL = 'Local Comercial'
    TERRENO = 'Terreno'


class Status(str, Enum):
    DISPONIBLE = 'Disponible'
    RESERVADO = 'Reservado'
    VENDIDO = 'Vendido'


@dataclass
class InmueblePhoto:
    url: str | None
    order: int = 0
    id: int | None = None


@dataclass
class Inmueble:
    title: str
    operation_type: OperationType
    property_type: PropertyType
    price: Decimal
    square_meters: Decimal
    location: str
    description: str
    id: int | None = None
    floor: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    parking_spots: int | None = None
    features: list[str] = field(default_factory=list)
    amenities: list[str] = field(default_factory=list)
    photos: list[InmueblePhoto] = field(default_factory=list)
    status: Status = Status.DISPONIBLE
    featured: bool = False
    created_at: datetime | None = None