import json
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent / 'data' / 'colombia_locations.json'

with open(_DATA_PATH, encoding='utf-8') as _f:
    CITIES_BY_DEPARTMENT: dict[str, list[str]] = json.load(_f)

DEPARTMENT_NAMES: list[str] = list(CITIES_BY_DEPARTMENT.keys())
