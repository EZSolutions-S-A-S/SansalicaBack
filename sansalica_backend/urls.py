"""
URL configuration for sansalica_backend project (versión minimalista de la
guía de arquitectura — ver settings.py).
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('maquillaje.api.urls')),
]
