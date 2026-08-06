# Capa API — URLS: el mapa de rutas.
#
# Le dice a Django "esta URL le corresponde a esta vista". Sin esto, aunque
# tengas el ViewSet perfecto, ninguna request sabría cómo llegar hasta él.
#
# El DefaultRouter de DRF genera automáticamente las rutas estándar de un
# CRUD a partir de un solo registro (list/create en la raíz, retrieve/update/
# destroy en /{id}/) — sin tener que escribir cada path() a mano, como sí
# habría que hacer con un ViewSet manual.
#
# Sigue el mismo patrón que inmuebles/api/urls.py.

from rest_framework.routers import DefaultRouter

from .views import MaquillajeViewSet

router = DefaultRouter()
router.register('maquillajes', MaquillajeViewSet, basename='maquillaje')

urlpatterns = router.urls

# Montado en sansalica_backend/urls.py como:
#   path('api/', include('maquillaje.api.urls'))
# → queda expuesto en /api/maquillajes/
