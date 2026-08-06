"""
Django settings for sansalica_backend project.

Esta es una versión MINIMALISTA del proyecto, pensada solo para correr el
ejemplo `maquillaje/` de la guía de arquitectura para practicantes. No tiene
JWT, CORS, R2 ni Postgres — esas piezas viven en la rama `andres_development`
(el proyecto real). Aquí el foco es la arquitectura por capas, no la
configuración de producción.

Para más información, ver https://docs.djangoproject.com/en/6.0/topics/settings/
"""

from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-plantilla-arquitectura')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'maquillaje',
]

# El paquete de migraciones vive en maquillaje/infrastructure/migrations
# (no en maquillaje/migrations) — mismo patrón que usa `inmuebles` en el
# proyecto real, para mantener las migraciones dentro de la capa infrastructure.
MIGRATION_MODULES = {
    'maquillaje': 'maquillaje.infrastructure.migrations',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
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


# Implementación concreta de ProductoRepository a usar (Dependency Inversion).
# Mismo mecanismo que INMUEBLE_REPOSITORY_CLASS en el proyecto real: para
# agregar un proveedor nuevo, se crea la clase en un archivo nuevo y se
# apunta este valor a su path — sin tocar composition.py ni la capa api/.
MAQUILLAJE_REPOSITORY_CLASS = config(
    'MAQUILLAJE_REPOSITORY_CLASS',
    default='maquillaje.infrastructure.repository.MaquillajeRepositoryImpl',
)
