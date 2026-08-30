"""
Django settings for sansalica_backend project.

App real `inmuebles/` — con API pública protegida por API Key, panel admin
JWT (pensado para un frontend Astro en subdominio propio), almacenamiento
de fotos en Cloudflare R2, y base de datos Postgres.

Para más información, ver https://docs.djangoproject.com/en/6.0/topics/settings/
"""

from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-plantilla-arquitectura')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Render (y la mayoría de PaaS) terminan el HTTPS por ti y reenvían la request
# a la app como HTTP puro, con este header indicando el protocolo original.
# Sin esto, Django no detecta HTTPS y las cookies seguras del admin nativo fallan.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Atados a DEBUG (no a variables nuevas): en local (DEBUG=True, HTTP) quedan
# apagados como ahora; en producción (DEBUG=False, siempre HTTPS) se activan solos.
# SECURE_HSTS_SECONDS se deja fuera a propósito para el primer deploy: Django
# advierte que activarlo con una config de HTTPS aún no confirmada puede dejar
# a los usuarios sin poder volver a HTTP durante todo ese tiempo.
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'inmuebles',
]

# El paquete de migraciones vive en <app>/infrastructure/migrations
# (no en <app>/migrations) — para mantener las migraciones dentro de la capa
# infrastructure, coherente con la arquitectura por capas del proyecto.
MIGRATION_MODULES = {
    'inmuebles': 'inmuebles.infrastructure.migrations',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Sirve los estáticos (CSS/JS del admin) directamente desde el proceso de
    # gunicorn en producción — no hay Nginx propio delante que los sirva.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sansalica_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sansalica_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

# Motor configurable 100% por variable de entorno (DATABASE_URL). Sin esa variable,
# se usa SQLite local como red de seguridad. Cambiar de motor no requiere tocar código.
# Se usa dj_database_url.parse() (no .config()) porque python-decouple lee el .env
# directamente sin exportarlo a os.environ, que es donde .config() buscaría la variable.
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
    )
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Agrega "code" (ErrorCode) a las respuestas de error de inmuebles/, sin
    # tocar el formato de los errores de auth/permisos ya existentes.
    'EXCEPTION_HANDLER': 'inmuebles.api.errors.custom_exception_handler',
}

# API Key para clientes de solo lectura (header: Authorization: Api-Key <token>)
READ_API_KEY = config('READ_API_KEY', default='')

# Implementación concreta de InmuebleRepository a usar (Dependency Inversion).
# Para agregar un proveedor nuevo, se crea la clase en un archivo nuevo y se
# apunta este valor a su path — sin tocar composition.py ni la capa api/.
INMUEBLE_REPOSITORY_CLASS = config(
    'INMUEBLE_REPOSITORY_CLASS',
    default='inmuebles.infrastructure.repository.DjangoInmuebleRepository',
)

# JWT para el panel de administración (Astro) — ver inmuebles/api/admin/
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'UPDATE_LAST_LOGIN': True,
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'TOKEN_OBTAIN_SERIALIZER': 'inmuebles.api.admin.serializers.StaffTokenObtainPairSerializer',
}

# CORS: orígenes permitidos para el panel admin (Astro). Autenticación por header
# Authorization (JWT), no por cookies, por lo que no se activa CORS_ALLOW_CREDENTIALS.
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())


# Almacenamiento de archivos (imágenes de propiedades)
# Cloudflare R2 es compatible con S3: se usa el backend S3Storage de django-storages
# apuntando al endpoint de R2. Si USE_R2_STORAGE es False, se usa almacenamiento local en disco.

USE_R2_STORAGE = config('USE_R2_STORAGE', default=False, cast=bool)

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

if USE_R2_STORAGE:
    R2_ACCOUNT_ID = config('R2_ACCOUNT_ID')
    R2_BUCKET_NAME = config('R2_BUCKET_NAME')
    R2_PUBLIC_URL = config('R2_PUBLIC_URL', default='')

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                'access_key': config('R2_ACCESS_KEY_ID'),
                'secret_key': config('R2_SECRET_ACCESS_KEY'),
                'bucket_name': R2_BUCKET_NAME,
                'endpoint_url': f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
                'region_name': 'auto',
                'custom_domain': R2_PUBLIC_URL.replace('https://', '').replace('http://', '') or None,
                'default_acl': None,
                'querystring_auth': not R2_PUBLIC_URL,
                'file_overwrite': False,
            },
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
