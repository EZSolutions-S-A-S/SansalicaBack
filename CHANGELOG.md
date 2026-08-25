# Changelog — rama `auth_r2_adjust`

Este documento explica todo lo que se agregó/corrigió en `inmuebles/` **después** de que se fusionó el trabajo base (`inmuebles_crud`, arquitectura por capas construida por Valentina/Isabel: dominio, casos de uso, modelo, repositorio, serializer y viewset básico). El objetivo era llevar esa base al punto de ser usable en producción: autenticación real, gestión de fotos en R2, conexión a Postgres, y validaciones.

---

## 0. Resumen paso a paso (orden real de construcción, desde autenticación)

### 1. Autenticación — dos mecanismos, cada uno para su caso de uso

1. **API Key para la API pública** (`inmuebles/api/authentication.py`): se creó `ReadOnlyApiKeyAuthentication`, que lee el header `Authorization: Api-Key <token>` y lo compara contra `READ_API_KEY` del `.env`. Si coincide, autentica con `user=None` (no representa a ningún usuario real, solo marca "cliente autorizado de solo lectura").
2. **Permiso que combina API Key + sesión staff** (`inmuebles/api/permissions.py`): se creó `ReadOnlyOrAdmin` — en métodos de lectura (`GET`/`HEAD`/`OPTIONS`) solo exige que algún autenticador haya tenido éxito (la API Key); en métodos de escritura exige `request.user.is_staff` real, así la API Key nunca puede escribir (su `user` siempre es `None`).
3. **Conectar ambos al viewset público** (`inmuebles/api/views.py`): `InmuebleViewSet` recibió `authentication_classes = [ReadOnlyApiKeyAuthentication]` y `permission_classes = [ReadOnlyOrAdmin]` (antes no tenía ninguno de los dos — estaba sin proteger).
4. **JWT para el panel admin** (paquete nuevo `inmuebles/api/admin/`): `permissions.py` (`IsStaffUser`, exige staff en todos los métodos), `serializers.py` (`StaffTokenObtainPairSerializer`, hereda de `simplejwt` y rechaza el login si el usuario no es staff antes de emitir el token), `views.py` (`AdminInmuebleViewSet`, CRUD completo + endpoints de fotos), `urls.py` (rutas `auth/login/`, `auth/refresh/` + rutas CRUD generadas por el router).
5. **Configurar JWT en settings** (`sansalica_backend/settings.py`): se agregó `rest_framework_simplejwt` a `INSTALLED_APPS` y el bloque `SIMPLE_JWT` (access token 15 min, refresh 7 días con rotación, apuntando a `StaffTokenObtainPairSerializer` como serializer de login).
6. **CORS** (para que el futuro frontend Astro pueda llamar la API): se agregó `django-cors-headers`, `corsheaders.middleware.CorsMiddleware` al `MIDDLEWARE`, y `CORS_ALLOWED_ORIGINS` leído del `.env`. Deliberadamente sin `CORS_ALLOW_CREDENTIALS`, porque la auth es por header (`Authorization`), no por cookies.

### 2. Almacenamiento de fotos (Cloudflare R2)

1. **Dependencias**: `django-storages[s3]` + `Pillow` (para validar imágenes reales, no solo la extensión).
2. **Settings**: bloque `STORAGES` condicional por `USE_R2_STORAGE` — si está en `True`, usa `S3Storage` apuntando al endpoint de R2; si no, cae a disco local. Nadie más en el código necesita saber cuál de los dos está activo.
3. **Dominio y contrato**: `InmueblePhoto` ganó un campo `id`; `InmuebleRepository` (la interfaz abstracta) ganó `add_photo`/`delete_photo`.
4. **Casos de uso** (`inmuebles/application/photo_use_cases.py`, nuevo): `AddInmueblePhoto` y `DeleteInmueblePhoto`, delegando al repositorio.
5. **Implementación real** (`inmuebles/infrastructure/repository.py`): `add_photo` valida que el inmueble exista, sube el archivo (`InmueblePhotoModel.objects.create(image=...)`), y devuelve la entidad de dominio. `delete_photo` borra primero el archivo físico del storage (`photo.image.delete(save=False)`) y luego la fila, para no dejar archivos huérfanos en R2.
6. **Endpoints dedicados** en `AdminInmuebleViewSet`: `POST /photos/` y `DELETE /photos/{photo_id}/`. Por esto se volvió `photos` de solo lectura en el serializer principal — ya no se suben fotos dentro del body de crear/editar un inmueble.

### 3. Base de datos — Postgres

1. Se agregaron `dj-database-url` y `psycopg[binary]`.
2. En `settings.py`, `DATABASES` pasó de un diccionario fijo de SQLite a `dj_database_url.parse(config('DATABASE_URL', default='sqlite:///...'))` — si `DATABASE_URL` no está en el `.env`, sigue cayendo a SQLite, así nadie se rompe por no configurarla.
3. Se conectó al contenedor Postgres compartido ya existente (`sansalica-api-postgres-1`, puerto 5544), pero en una base de datos propia (`sansalica_backend`) separada de la del proyecto Laravel, para no chocar datos.

### 4. Validaciones y códigos de error (lo último que se agregó)

1. Se identificaron 3 huecos: mismatch de `max_digits` en `price`, ausencia de reglas de negocio (precios/áreas en cero o negativos, habitaciones negativas), y `?page=abc` tirando `500` sin manejar.
2. `inmuebles/api/errors.py` (nuevo): enum `ErrorCode` en inglés + excepciones propias (`InvalidPageError`, `InvalidPageSizeError`, `InvalidPriceRangeError`) + validadores reusables (`MustBePositive`, `MustBeNonNegative`) + `custom_exception_handler`, que agrega el `code` a la respuesta solo para estos casos nuevos, sin tocar el formato ya existente de los errores 401/403.
3. Se conectó vía `EXCEPTION_HANDLER` en `REST_FRAMEWORK` (`settings.py`).
4. Se aplicaron los validadores en `serializers.py` (price/square_meters/bedrooms/bathrooms/parking_spots) y el manejo de `try/except` en `views.py` y `admin/views.py` para page/page_size/min_price/max_price.

---

## 1. Bugs corregidos

### Migraciones no se cargaban
**Qué pasaba**: `inmuebles/domain/`, `inmuebles/application/`, `inmuebles/infrastructure/` e `inmuebles/infrastructure/migrations/` no tenían archivo `__init__.py`. Python los trataba como "paquetes de espacio de nombres" en vez de paquetes normales, y el cargador de migraciones de Django ignora silenciosamente esos casos — trataba la app como si no tuviera ninguna migración.

**Por qué importa**: apenas alguien conectara la app (`INSTALLED_APPS`) e intentara migrar, Django hubiera intentado generar `0001_initial.py` desde cero, chocando con la migración que ya existía.

**Solución**: se agregaron los 4 `__init__.py` faltantes.

### `PATCH` parcial rompía con error 500
**Qué pasaba**: `InmuebleSerializer.update()` reconstruía la entidad completa a partir de `validated_data` en vez de modificar solo los campos enviados. Un `PATCH` con un solo campo (ej. `{"price": 100}`) producía `KeyError` porque faltaban los demás campos requeridos.

**Solución**: se cambió a fusionar los campos recibidos sobre la instancia existente (`setattr` por cada campo presente), en vez de reconstruir todo desde cero.

### Las fotos se aceptaban pero nunca se guardaban
**Qué pasaba**: el campo `photos` del serializer era escribible, pero ni `create()` ni `update()` del repositorio lo usaban — cualquier foto enviada en el body se validaba y se descartaba en silencio.

**Solución**: se volvió `photos` de solo lectura (se gestionan por endpoints dedicados, ver sección 3) y se corrigió el mismatch de `price` entre el serializer (permitía 12 dígitos) y el modelo (permitía 14) de paso.

---

## 2. Autenticación — dos mecanismos, cada uno para su uso

### API Key para lectura pública (`/api/inmuebles/`)
Un solo token fijo (`READ_API_KEY` en `.env`), pensado para clientes externos de solo lectura (ej. el sitio web público). Se manda como `Authorization: Api-Key <token>`. No requiere usuario ni sesión — o tienes el token correcto, o no entras.

**Archivos nuevos**: `inmuebles/api/authentication.py` (`ReadOnlyApiKeyAuthentication`), `inmuebles/api/permissions.py` (`ReadOnlyOrAdmin`).

### JWT para el panel admin (`/api/admin/`)
Login real con usuario/contraseña de staff, pensado para un futuro frontend (Astro) en subdominio propio. Devuelve un token de acceso (15 min) y uno de refresco (7 días, con rotación).

**Archivos nuevos**: paquete completo `inmuebles/api/admin/` — `permissions.py` (`IsStaffUser`), `serializers.py` (`StaffTokenObtainPairSerializer`, rechaza login de no-staff), `views.py` (`AdminInmuebleViewSet`, CRUD completo), `urls.py` (login/refresh + rutas CRUD).

---

## 3. Gestión de fotos (Cloudflare R2)

Como las fotos ya no se pueden mandar dentro del body de crear/editar un inmueble, se agregaron endpoints propios:
- `POST /api/admin/inmuebles/{id}/photos/` (multipart) — sube una foto.
- `DELETE /api/admin/inmuebles/{id}/photos/{photo_id}/` — la borra (del archivo real en R2, no solo de la base de datos).

**Cambios en el dominio**: `InmueblePhoto` ganó un campo `id` (para poder referenciar una foto específica). El contrato `InmuebleRepository` ganó `add_photo`/`delete_photo`.

**Archivos nuevos**: `inmuebles/application/photo_use_cases.py` (`AddInmueblePhoto`, `DeleteInmueblePhoto`).

**Almacenamiento**: `sansalica_backend/settings.py` tiene el bloque `STORAGES` — si `USE_R2_STORAGE=True`, las fotos van a Cloudflare R2 (S3-compatible); si no, a disco local. El modelo (`InmueblePhotoModel.image`, un `ImageField` normal) no sabe ni le importa cuál de los dos se está usando.

---

## 4. Base de datos — Postgres

Antes esta rama usaba SQLite fijo. Se agregó soporte para Postgres vía una variable de entorno (`DATABASE_URL`), usando `dj-database-url` para parsearla — si la variable no está presente, sigue cayendo a SQLite local (sin romper a nadie que no la configure).

En la práctica, esta app se conecta al mismo contenedor Postgres que ya usa el proyecto Laravel del equipo, pero en su propia base de datos (`sansalica_backend`, separada de la de Laravel) para no chocar con esos datos.

---

## 5. Validaciones y códigos de error

### Reglas de negocio nuevas
- `price` y `square_meters` deben ser mayores a 0.
- `bedrooms`, `bathrooms`, `parking_spots` no pueden ser negativos (`floor` sí puede, para sótanos).
- `?page=`, `?page_size=`, `?min_price=`, `?max_price=` inválidos ahora devuelven `400` con un mensaje claro, en vez de un `500` sin manejar.

### Sistema de códigos de error
Se agregó `inmuebles/api/errors.py` con un enum `ErrorCode` (en inglés) y clases de excepción propias, para que cualquier error de validación venga con un código identificable además del mensaje — útil para que un frontend distinga programáticamente *qué* regla falló, no solo que algo falló.

Ejemplo:
```json
{"price": [{"message": "Price must be greater than 0.", "code": "must_be_positive"}]}
```

Esto se conecta a través de un `EXCEPTION_HANDLER` personalizado en `settings.py`, diseñado para **no tocar** el formato de los errores de autenticación/permisos que ya existían (`403`/`401` siguen exactamente igual).

---

## 6. Infraestructura local

`docker-compose.yml` — Postgres local para desarrollo (nota: usa el puerto `5544`, el mismo que ya ocupa el contenedor compartido con Laravel — no correr ambos a la vez sin ajustar el puerto).

---

## Todo probado de punta a punta

Cada pieza de este changelog se probó manualmente contra el servidor real antes de commitear: login JWT, API Key pública, CRUD completo, subida/borrado de fotos contra el bucket R2 real, conexión a Postgres, y los 5 casos nuevos de validación — sin regresiones en lo que ya funcionaba.

---

## Anexo: explicación línea por línea del código

### `inmuebles/api/authentication.py` (autenticación pública)

```python
from django.conf import settings
from rest_framework import authentication
```
Importa `settings` para leer `READ_API_KEY`, y el módulo `authentication` de DRF (de ahí sale `BaseAuthentication`, la clase que hay que heredar para crear un mecanismo de auth propio).

```python
class ReadOnlyApiKeyAuthentication(authentication.BaseAuthentication):
    keyword = 'Api-Key'
```
`keyword` define qué palabra debe aparecer al inicio del header `Authorization`. Como es `'Api-Key'`, el header esperado es `Authorization: Api-Key <token>` (si dijera `'Bearer'` sería `Authorization: Bearer <token>`, como JWT).

```python
    def authenticate(self, request):
```
DRF llama este método en **cada** request. Debe devolver `(user, auth)` si autentica bien, `None` si no aplica (deja pasar a la siguiente clase de auth), o lanzar una excepción si quiere rechazar activamente.

```python
        header = authentication.get_authorization_header(request).decode('utf-8')
```
Lee el header `Authorization` crudo (viene en bytes) y lo convierte a string normal.

```python
        if not header or not header.startswith(f'{self.keyword} '):
            return None
```
Si no hay header, o no empieza con `"Api-Key "` (con el espacio), no es nuestro tipo de auth — devuelve `None` para que DRF siga probando otros mecanismos (o termine sin autenticar a nadie).

```python
        token = header[len(self.keyword) + 1:].strip()
```
Corta el string desde después de `"Api-Key "` (longitud de la palabra + 1 por el espacio) y le quita espacios sobrantes — así se queda solo con el valor del token.

```python
        if not settings.READ_API_KEY or token != settings.READ_API_KEY:
            return None
```
Si `READ_API_KEY` no está configurado en el `.env`, o el token no coincide exactamente, tampoco autentica.

```python
        return (None, token)
```
Si todo coincide, devuelve una tupla `(user, auth)`. El primer valor (`user`) es `None` a propósito — **no representa a ningún usuario real**, es un cliente genérico autorizado. El segundo (`auth`, aquí `token`) queda disponible como `request.auth` por si se necesitara luego. Lo importante es que DRF, al recibir una tupla no-`None`, marca `request.successful_authenticator` — que es justo lo que lee `ReadOnlyOrAdmin` para decidir si dejar pasar la lectura.

### `inmuebles/api/permissions.py` (permiso público)

```python
class ReadOnlyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.successful_authenticator)

        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
```
- `SAFE_METHODS` es una constante de DRF = `('GET', 'HEAD', 'OPTIONS')` (los métodos que no modifican datos).
- Si el método es de lectura → solo importa que **algún** autenticador haya tenido éxito (`request.successful_authenticator` no sea `None`) — no le importa cuál. Como el único autenticador configurado en el viewset es la API Key, en la práctica esto es "¿la API Key fue válida?".
- Si el método es de escritura (POST/PUT/PATCH/DELETE) → exige que exista un `request.user` real, autenticado, y que sea staff. Esto es deliberado: la API Key **nunca** puede escribir, porque `authenticate()` siempre devuelve `user=None` — un `None` nunca cumple `request.user.is_authenticated`.

### `inmuebles/api/admin/permissions.py` (permiso admin)

```python
class IsStaffUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
```
Más simple que el anterior: **todo** método (lectura o escritura) exige usuario autenticado y staff — no hay excepción para lectura, porque este namespace entero es privado.

### `inmuebles/api/admin/serializers.py` (login JWT)

```python
class StaffTokenObtainPairSerializer(TokenObtainPairSerializer):
```
Hereda de la clase que trae `djangorestframework-simplejwt` — no reescribimos la lógica de generar tokens, solo le agregamos una capa encima.

```python
    def validate(self, attrs):
        data = super().validate(attrs)
```
`super().validate(attrs)` ejecuta la validación original de la librería: verifica usuario/contraseña contra la base de datos, y si son correctos, genera los tokens `access`/`refresh`. Si la contraseña está mal, esta línea ya lanza una excepción por su cuenta — nunca llegamos a la siguiente línea.

```python
        if not self.user.is_staff:
            raise AuthenticationFailed('Solo usuarios staff pueden acceder al panel de administración.')
        return data
```
`self.user` lo deja seteado la librería padre tras validar credenciales. Si el usuario existe y la contraseña es correcta, pero **no** es staff, igual lo rechazamos aquí — antes de devolver ningún token. Por eso un usuario normal (no staff) nunca puede obtener un JWT admin, ni siquiera uno "inútil".

```python
class InmueblePhotoUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    order = serializers.IntegerField(required=False, default=0)
```
Serializer chico, solo para validar el body del endpoint de subir foto. `ImageField()` no solo comprueba que venga un archivo — usa Pillow por debajo para confirmar que el contenido sea una imagen real y decodificable, no cualquier archivo con extensión `.jpg`.

### `inmuebles/api/admin/urls.py`

```python
router = DefaultRouter()
router.register('inmuebles', AdminInmuebleViewSet, basename='admin-inmueble')
```
`DefaultRouter` de DRF genera automáticamente las rutas estándar de un ViewSet (list/create en la raíz, retrieve/update/destroy en `/{id}/`) sin que tengamos que escribir cada `path()` a mano. `basename='admin-inmueble'` es solo el nombre interno que usa Django para poder referenciar estas rutas por nombre en otro lado (no afecta la URL en sí).

```python
urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='admin-token-obtain-pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='admin-token-refresh'),
] + router.urls
```
`TokenObtainPairView`/`TokenRefreshView` son vistas que ya vienen completas en `simplejwt` — no escribimos ninguna lógica de login/refresh nosotros, solo las conectamos a estas dos rutas. `+ router.urls` concatena la lista de rutas del CRUD a las dos de auth, formando la lista completa que Django monta.

### `inmuebles/api/errors.py` (sistema de errores)

```python
class ErrorCode(str, Enum):
    INVALID_PAGE = 'invalid_page'
    ...
```
Al heredar de `str` además de `Enum`, cada miembro se comporta como un string normal (`ErrorCode.INVALID_PAGE == 'invalid_page'` da `True`), lo cual hace que se pueda meter directo en un JSON sin conversión extra.

```python
class InmuebleAPIException(APIException):
    code: ErrorCode

    def __init__(self, detail=None):
        super().__init__(detail=detail or self.default_detail)
```
`code: ErrorCode` es solo una anotación de tipo (documentación), no crea el atributo — cada subclase concreta lo define de verdad (ej. `code = ErrorCode.INVALID_PAGE`). El `__init__` permite lanzar la excepción sin argumentos (`raise InvalidPageError()`) y usar automáticamente `default_detail`, o pasar un mensaje custom si algún día hiciera falta.

```python
class InvalidPageError(InmuebleAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The 'page' parameter must be a valid integer."
    code = ErrorCode.INVALID_PAGE
```
Cada excepción concreta solo define 3 cosas: el status HTTP, el mensaje, y el código. Nada de lógica propia — toda la lógica vive en la clase base.

```python
class MustBePositive:
    def __init__(self, message: str):
        self.message = message

    def __call__(self, value):
        if value <= 0:
            raise serializers.ValidationError(self.message, code=ErrorCode.MUST_BE_POSITIVE.value)
```
Esto **no** es una excepción — es un *validador* de DRF: cualquier objeto con `__call__(self, value)` sirve como validador de un campo (`validators=[MustBePositive(...)]` en el serializer). DRF lo llama automáticamente con el valor ya parseado del campo, y si lanza `ValidationError`, DRF lo captura y arma la respuesta `400` con el detalle bajo el nombre del campo correspondiente.

```python
def _attach_codes(data):
    if isinstance(data, list):
        result = []
        for item in data:
            if isinstance(item, (dict, list)):
                result.append(_attach_codes(item))
            else:
                result.append({'message': str(item), 'code': getattr(item, 'code', None) or 'invalid'})
        return result
    if isinstance(data, dict):
        return {key: _attach_codes(value) for key, value in data.items()}
    return data
```
Esta función recorre recursivamente la estructura de errores que arma DRF. Un error de validación normal luce así internamente: `{"price": [ErrorDetail("Price must be...", code='must_be_positive')]}` — `ErrorDetail` es un `str` con un `.code` pegado, pero por defecto DRF solo muestra el texto, no el código, en la respuesta JSON. Esta función camina el diccionario/lista, y donde encuentra un `ErrorDetail` (el `else` final), lo convierte en `{"message": ..., "code": ...}`, exponiendo el código que ya existía pero estaba oculto.

```python
def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return response
```
Primero deja que DRF haga su procesamiento normal (arma el `Response` con el status code correcto, etc.). Si DRF no supo qué hacer con la excepción (`response is None`, ej. un error de Python no relacionado a la API), no tocamos nada — se deja que reviente como excepción normal de Django (500 real, visible en logs).

```python
    if isinstance(exc, InmuebleAPIException):
        response.data['code'] = exc.code.value
    elif isinstance(exc, ValidationError):
        response.data = _attach_codes(response.data)

    return response
```
Esta es la parte que decide **cuándo** se agrega el código. Si es una de nuestras 3 excepciones custom (page/page_size/price_range) → agrega `code` directo al nivel superior del JSON. Si es un `ValidationError` (errores de campo del serializer, incluidos los de `MustBePositive`/`MustBeNonNegative`) → recorre y agrega códigos por cada campo. **Cualquier otra excepción** (como `NotAuthenticated`, `PermissionDenied`, que no son ninguna de las dos) simplemente no entra a ninguna rama — el `response` sale exactamente igual a como lo armó DRF por defecto, sin ningún `code` agregado. Por eso el `403`/`401` de siempre queda intacto.

### `inmuebles/api/serializers.py` (validaciones + fix del PATCH)

```python
price = serializers.DecimalField(
    max_digits=14, decimal_places=2,
    validators=[MustBePositive('Price must be greater than 0.')],
)
```
`max_digits=14` (antes 12) para que coincida con el modelo. `validators=[...]` engancha el validador reutilizable — DRF lo corre automáticamente después de confirmar que el valor es un decimal válido, antes de aceptarlo como bueno.

```python
floor = serializers.IntegerField(required=False, allow_null=True)
```
Sin `validators=[...]` — a propósito, para permitir sótanos negativos, como dice el comentario en el código.

```python
def update(self, instance, validated_data):
    for attr, value in validated_data.items():
        if attr == 'operation_type':
            value = OperationType(value)
        elif attr == 'property_type':
            value = PropertyType(value)
        elif attr == 'status':
            value = Status(value)
        setattr(instance, attr, value)
    return instance
```
Este es el fix del bug de `PATCH`. Recorre **solo** los campos que de verdad vinieron en el request (`validated_data` en un PATCH parcial solo contiene lo enviado, nunca todos los campos), y los va poniendo uno por uno sobre la instancia existente (`setattr`) — así los campos no enviados quedan intactos con su valor anterior. El `if/elif` es necesario porque `operation_type`/`property_type`/`status` en el JSON llegan como texto plano (`"Venta"`), pero la entidad de dominio los espera como el `Enum` correspondiente (`OperationType.VENTA`) — sin esta conversión, quedarían guardados como string suelto en vez de Enum, rompiendo la consistencia de tipos en el resto del código.

### `inmuebles/api/views.py` (query params)

```python
try:
    min_price = Decimal(min_price) if min_price else None
    max_price = Decimal(max_price) if max_price else None
except InvalidOperation:
    raise InvalidPriceRangeError()
```
`Decimal("xyz")` lanza `InvalidOperation` (no `ValueError`, es una excepción propia del módulo `decimal`) cuando el string no es un número válido. Si `min_price`/`max_price` no vinieron en absoluto (`None`/string vacío), el `if min_price else None` los deja como `None` sin intentar convertir nada.

```python
try:
    page = int(request.query_params.get('page', 1))
except ValueError:
    raise InvalidPageError()
```
Antes esto no tenía `try/except` — si `page=abc`, `int("abc")` lanzaba `ValueError` sin capturar, y Django lo convertía en un `500` genérico. Ahora se captura explícitamente y se relanza como nuestra excepción propia, que el `custom_exception_handler` convierte en un `400` limpio con código.

### `inmuebles/domain/entities.py` y `repositories.py` (fotos)

```python
@dataclass
class InmueblePhoto:
    url: str | None
    order: int = 0
    id: int | None = None
```
Se agregó `id` al final (con default `None`) — un cambio aditivo seguro: como tiene valor por defecto, ningún código que ya construía `InmueblePhoto(url=..., order=...)` sin pasar `id` se rompe.

```python
@abstractmethod
def add_photo(self, inmueble_id: int, image_file, order: int = 0) -> InmueblePhoto | None:
    """Crea una foto asociada a un inmueble. Devuelve None si el inmueble no existe."""
    ...

@abstractmethod
def delete_photo(self, photo_id: int) -> bool:
    ...
```
Dos métodos nuevos en el contrato abstracto — cualquier implementación futura del repositorio (no solo la de Django) está obligada a implementarlos, o Python no la deja instanciar.

### `inmuebles/infrastructure/repository.py` (implementación de fotos)

```python
def add_photo(self, inmueble_id: int, image_file, order: int = 0) -> InmueblePhoto | None:
    if not InmuebleModel.objects.filter(id=inmueble_id).exists():
        return None
```
Primero verifica que el inmueble exista de verdad — si alguien intenta subir una foto a un `id` inexistente, devuelve `None` en vez de crear una foto huérfana apuntando a nada.

```python
    photo = InmueblePhotoModel.objects.create(inmueble_id=inmueble_id, image=image_file, order=order)
```
`InmueblePhotoModel.objects.create(...)` — al pasarle `image=image_file` (un archivo de Django, `ImageField` sabe manejarlo), Django automáticamente lo sube al storage configurado en `STORAGES` (R2 o disco local, según `USE_R2_STORAGE`). Esta línea es la única que realmente "sube el archivo" — todo lo de arriba (settings, serializer) solo prepara el terreno para que esta línea funcione.

```python
    return InmueblePhoto(id=photo.id, url=self._photo_url(photo), order=photo.order)
```
Convierte el modelo recién creado (`InmueblePhotoModel`, un objeto de Django/ORM) a la entidad de dominio pura (`InmueblePhoto`) — así lo que sale de esta función nunca expone detalles de Django hacia arriba.

```python
def delete_photo(self, photo_id: int) -> bool:
    photo = InmueblePhotoModel.objects.filter(id=photo_id).first()
    if not photo:
        return False

    photo.image.delete(save=False)
    photo.delete()
    return True
```
Dos borrados distintos: `photo.image.delete(save=False)` borra el **archivo físico** del storage (R2 o disco) — `save=False` le dice a Django que no intente además guardar el modelo con el campo vacío, porque de inmediato lo vamos a borrar completo con `photo.delete()` (borra la **fila** de la base de datos). Sin la primera línea, el archivo se queda huérfano en el bucket para siempre, ocupando espacio, aunque ya no exista ningún registro que lo referencie.

### `sansalica_backend/settings.py` (wiring)

```python
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
    )
}
```
`config('DATABASE_URL', default=...)` lee la variable del `.env` (vía `python-decouple`); si no existe, usa el default (una URL de SQLite apuntando al archivo local). `dj_database_url.parse(...)` toma esa URL como texto (`postgres://user:pass@host:port/db` o `sqlite:///ruta`) y la convierte al diccionario que Django realmente necesita en `DATABASES['default']` (`ENGINE`, `NAME`, `USER`, etc.) — sin esto, tendríamos que escribir ese diccionario a mano y no podríamos cambiar de motor solo con una variable de entorno.

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [...],
    'EXCEPTION_HANDLER': 'inmuebles.api.errors.custom_exception_handler',
}
```
Esta única línea es la que activa todo el sistema de códigos de error — le dice a DRF "cuando cualquier vista lance una excepción, en vez de tu manejador por defecto, usa este". Sin esta línea, `custom_exception_handler` existiría en el código pero nunca se ejecutaría.

```python
if USE_R2_STORAGE:
    ...
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                ...
                'querystring_auth': not R2_PUBLIC_URL,
```
`querystring_auth` controla si las URLs de las fotos llevan una firma temporal (`?X-Amz-Signature=...`) que expira, o son URLs públicas permanentes. Si configuraste un dominio público (`R2_PUBLIC_URL`), no hace falta firmar nada — por eso es `not R2_PUBLIC_URL` (si hay dominio público, `querystring_auth` queda en `False`).
