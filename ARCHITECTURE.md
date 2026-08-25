# Guía de arquitectura — Sansalica Backend

- **`maquillaje/`** (raíz del repo) — un catálogo de maquillaje: código real, sin `TODO`, ya corriendo dentro de este mismo proyecto (`python manage.py runserver` lo expone en `/api/maquillajes/`). Es la "hoja de respuestas": léelo, cópialo, pruébalo con el navegador o Postman, y compáralo contra tu propio avance en `inmuebles/`.
- **`inmuebles/`** (raíz del repo) — el mismo patrón, pero es **tu ejercicio real**: la estructura de carpetas y archivos ya está creada, con comentarios explicando qué va en cada método, pero la lógica está en `TODO`. Aquí es donde construyes la funcionalidad real del catálogo de inmuebles de Sansalica. **No está registrada en `INSTALLED_APPS` todavía a propósito** — es parte de tu ejercicio dejarla corriendo.

No necesitas memorizar nada de esto de una vez — vuelve a este documento cada vez que no sepas en qué carpeta poner algo.

---

## 1. La idea central: capas y flujo de dependencias

El proyecto sigue **arquitectura limpia** (Clean Architecture): el código se separa en 4 capas, y las dependencias solo pueden apuntar "hacia adentro":

```
        api  ──────►  application  ──────►  domain  ◄──────  infrastructure
   (HTTP, DRF)         (casos de uso)     (reglas puras,        (Django ORM,
                                            sin Django)           base de datos)
```

**Regla de oro**: `domain` no depende de nada del proyecto. Todo lo demás depende de `domain`, directa o indirectamente. `infrastructure` nunca es importado directamente por `api` — siempre hay un paso intermedio (ver sección de desacoplamiento).

### ¿Por qué separar así?

Porque cada capa cambia por una razón distinta:
- Cambias la base de datos (SQLite → Postgres) → solo tocas `infrastructure`.
- Cambias cómo se expone la API (agregar un endpoint, cambiar un filtro) → solo tocas `api`.
- Cambias una regla de negocio (ej. "un inmueble no puede tener precio negativo") → solo tocas `domain`/`application`.

Si todo estuviera mezclado en un solo archivo `views.py` gigante, cualquier cambio pequeño arriesga romper algo en otra parte.

---

## 2. Qué va en cada carpeta

| Carpeta | Responsabilidad | Puede importar | NUNCA debe importar |
|---|---|---|---|
| `domain/` | Las "reglas del negocio" en su forma más pura: qué es un Inmueble, qué campos tiene, qué operaciones existen conceptualmente (listar, crear, etc.) | Solo Python puro (`dataclasses`, `enum`, `abc`, `datetime`, `decimal`) | Django, DRF, o cualquier cosa de `infrastructure`/`application`/`api` |
| `application/` | Los "casos de uso": qué pasa cuando alguien quiere listar/crear/editar/borrar. Es la orquestación, no la implementación | Solo `domain` (las entidades y la interfaz del repositorio) | Django, DRF, o la clase concreta de `infrastructure` |
| `infrastructure/` | Cómo se guardan los datos de verdad: modelos de Django, migraciones, la implementación real del repositorio, registro en Django Admin | Django (`models`, `admin`, ORM), y `domain` (para implementar su interfaz) | `application` o `api` — nunca llama "hacia afuera" |
| `api/` | La puerta de entrada HTTP: serializers, permisos, autenticación, viewsets, urls | DRF, `application` (casos de uso), `domain` (para tipos), y `composition.py` (para obtener un repositorio) | La clase concreta de `infrastructure` directamente — solo a través de `composition.py` |

### Ejemplo de a qué se refiere "no debe importar"

❌ **Mal** — un archivo de `domain/entities.py` que hace esto:
```python
from django.db import models  # una entidad de dominio jamás debe saber que existe Django
```

✅ **Bien** — un archivo de `domain/entities.py` que solo usa:
```python
from dataclasses import dataclass
from decimal import Decimal
```

---

## 3. Desacoplamiento (Dependency Inversion) — el porqué, con ejemplos reales

Esta es la parte más importante y la que más cuesta entender al principio. Se explica con el ejemplo real ya construido en `inmuebles/` en la rama `andres_development` (donde vive la versión funcionando de este mismo catálogo).

### El problema: acoplamiento directo

Imagina que un `ViewSet` (capa `api`) hiciera esto:

```python
# api/views.py
from infrastructure.repository import DjangoInmuebleRepository  # ❌ import directo de la clase concreta

class InmuebleViewSet(viewsets.ViewSet):
    def _repository(self):
        return DjangoInmuebleRepository(request=self.request)  # ❌ construye la clase concreta a mano
```

¿Qué problema tiene esto? Que **todos** los archivos que hacen esto (puede haber varios viewsets) quedan "pegados" a esa clase concreta. Si un día cambias la forma de guardar los datos (por ejemplo, para escribir pruebas automáticas con una versión falsa en memoria), tienes que ir archivo por archivo cambiando el import y la construcción. Cuantos más archivos hagan esto, más frágil se vuelve el proyecto.

### La solución: depender de una interfaz, no de una clase concreta

En `domain/repositories.py` se define una interfaz (una clase abstracta, `ABC`) que dice **qué** debe poder hacer cualquier repositorio, sin decir **cómo**:

```python
# domain/repositories.py
class InmuebleRepository(ABC):
    @abstractmethod
    def list(self, filters, page, page_size): ...
    @abstractmethod
    def get(self, inmueble_id): ...
    @abstractmethod
    def create(self, inmueble): ...
    # ...etc
```

`application/use_cases.py` recibe esta interfaz en su constructor, nunca la clase concreta:

```python
class ListInmuebles:
    def __init__(self, repository: InmuebleRepository):  # el tipo es la interfaz, no DjangoInmuebleRepository
        self.repository = repository
```

Y `infrastructure/repository.py` es quien **implementa** esa interfaz con Django de verdad:

```python
class DjangoInmuebleRepository(InmuebleRepository):
    def list(self, filters, page, page_size):
        # aquí sí hay Django ORM de verdad
        ...
```

Ni `application` ni `domain` saben que `DjangoInmuebleRepository` existe. Solo saben que "algo" implementa `InmuebleRepository`.

### El punto único de conexión: `composition.py`

Si nadie en `application`/`api` conoce la clase concreta, ¿quién decide cuál usar? Un solo archivo, `composition.py`:

```python
# composition.py
from django.conf import settings
from django.utils.module_loading import import_string

def get_inmueble_repository(request=None):
    repository_class = import_string(settings.INMUEBLE_REPOSITORY_CLASS)  # lee el nombre de settings
    return repository_class(request=request)
```

Y en `settings.py` hay un valor configurable:
```python
INMUEBLE_REPOSITORY_CLASS = config(
    'INMUEBLE_REPOSITORY_CLASS',
    default='inmuebles.infrastructure.repository.DjangoInmuebleRepository',
)
```

Ahora el `ViewSet` queda así:
```python
# api/views.py
from composition import get_inmueble_repository  # ✅ ya no importa la clase concreta

class InmuebleViewSet(viewsets.ViewSet):
    def _repository(self):
        return get_inmueble_repository(request=self.request)  # ✅ no sabe qué clase es realmente
```

### Por qué esto importa: "agregar sin modificar"

Si mañana quieres agregar una implementación nueva (por ejemplo, un repositorio falso para pruebas automáticas), el proceso es:

1. Crear una clase nueva que implemente `InmuebleRepository` (un archivo nuevo).
2. Cambiar el valor de `INMUEBLE_REPOSITORY_CLASS` en `.env`.
3. **Cero archivos existentes se tocan.**

Esto se llama el **principio abierto/cerrado**: el sistema está abierto a extensión (puedes agregar cosas nuevas) pero cerrado a modificación (no tienes que editar lo que ya funciona).

### Segundo ejemplo, mismo patrón: la base de datos

El mismo truco se usa para el motor de base de datos. En vez de tener esto hardcodeado en `settings.py`:
```python
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', ...}}  # ❌ fijo en el código
```

Se usa una variable de entorno:
```python
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
    )
}
```

Con esto, pasar de SQLite (desarrollo local) a Postgres (producción) es cambiar una variable en `.env` (`DATABASE_URL=postgres://...`), no tocar código. Es el mismo principio que el repositorio, aplicado a un lugar distinto — para que veas que no es un truco aislado, sino una forma de pensar que se repite.

---

## 4. Cómo usar los ejemplos de esta guía

### `maquillaje/` — el ejemplo funcional, para leer y correr

Este es código real corriendo en este mismo proyecto. Para verlo con tus propios ojos:

```bash
python manage.py migrate
python manage.py runserver
```

Y luego, en otra terminal (o Postman):
```bash
curl http://127.0.0.1:8000/api/maquillajes/
curl -X POST http://127.0.0.1:8000/api/maquillajes/ -H "Content-Type: application/json" -d "{\"nombre\":\"Labial Rojo\",\"categoria\":\"Labial\",\"precio\":15.99,\"marca\":\"Sansalica Beauty\"}"
```

Para entender el patrón, lee los archivos en este orden (así vas de "qué es un Maquillaje" hacia "cómo llega por HTTP"): `domain/entities.py` → `domain/repositories.py` → `application/use_cases.py` → `infrastructure/models.py` → `infrastructure/repository.py` → `composition.py` → `api/`. Cada archivo tiene un comentario de cabecera explicando su responsabilidad.

### `inmuebles/` — tu ejercicio real

Ya existe la misma estructura de carpetas, con los mismos comentarios explicando qué va en cada capa. Tu trabajo es reemplazar los `TODO` por la lógica real, capa por capa — usando `maquillaje/` como referencia línea por línea si te trabas:

1. Empieza por `domain/entities.py` y `domain/repositories.py` — define qué es un Inmueble y qué operaciones necesita.
2. Sigue con `infrastructure/models.py` — el modelo real de Django.
3. Implementa `infrastructure/repository.py` — la clase que cumple la interfaz de `domain/repositories.py` usando el modelo de Django.
4. Implementa `application/use_cases.py` — cada caso de uso solo debe llamar al repositorio, sin lógica compleja.
5. Termina con `api/` — serializers, permisos, viewset, urls.
6. Registra la app en `sansalica_backend/settings.py` y `urls.py` — ver la sección 5 abajo, es exactamente el mismo procedimiento que se usó para conectar `maquillaje`.

No te preocupes por hacerlo perfecto a la primera — la idea es que practiques el patrón completo, de principio a fin.

---

## 5. Cómo se conecta `maquillaje` con el resto del proyecto

Tener las carpetas de `maquillaje/` bien armadas no es suficiente para que Django las use — hay 5 puntos de conexión en `sansalica_backend/`. Estos son los cambios reales que se hicieron para dejarlo corriendo (los mismos que tendrás que replicar para `inmuebles/`):

**1. Registrar la app en `INSTALLED_APPS`** (`sansalica_backend/settings.py`):
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'maquillaje',   # ← esta línea
]
```
Sin esto, Django ni siquiera sabe que la app existe.

**2. Un archivo `models.py` en la raíz de la app** (`maquillaje/models.py`) — Django busca los modelos ahí por convención, no dentro de `infrastructure/`:
```python
from .infrastructure.models import MaquillajeModel

__all__ = ['MaquillajeModel']
```
Este archivo es solo un "reenvío" (shim) — la implementación real sigue viviendo en `infrastructure/models.py`. Sin este shim, `python manage.py makemigrations` no detecta ningún modelo y dice "No changes detected" aunque el modelo exista.

**3. Redirigir las migraciones a `infrastructure/migrations/`** (`sansalica_backend/settings.py`) — si no, Django esperaría encontrarlas en `maquillaje/migrations/`:
```python
MIGRATION_MODULES = {
    'maquillaje': 'maquillaje.infrastructure.migrations',
}
```

**4. Montar las rutas** (`sansalica_backend/urls.py`):
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('maquillaje.api.urls')),
]
```

**5. El setting de desacoplamiento** (`sansalica_backend/settings.py`), mismo mecanismo que `INMUEBLE_REPOSITORY_CLASS` explicado en la sección 3, ahora en un segundo lugar del código para reforzar que no es un caso aislado:
```python
MAQUILLAJE_REPOSITORY_CLASS = config(
    'MAQUILLAJE_REPOSITORY_CLASS',
    default='maquillaje.infrastructure.repository.MaquillajeRepositoryImpl',
)
```

Con estos 5 puntos, `python manage.py makemigrations maquillaje` genera la migración, `migrate` crea la tabla, y `/api/maquillajes/` queda vivo.

---

## 6. Errores comunes a evitar

- ❌ Importar `django.db.models` (o cualquier cosa de Django) dentro de `domain/`.
- ❌ Importar la clase concreta del repositorio (`DjangoXxxRepository`) en cualquier archivo de `api/` — siempre a través de `composition.py`.
- ❌ Poner lógica de negocio dentro de un serializer o de un viewset — esa lógica va en `application/use_cases.py`.
- ❌ Hardcodear un valor (motor de base de datos, nombre de clase, credencial) que debería venir de una variable de entorno cuando ya existe el mecanismo para eso.
- ❌ Que `application/` llame directamente a un modelo de Django — siempre debe pasar por la interfaz del repositorio.
