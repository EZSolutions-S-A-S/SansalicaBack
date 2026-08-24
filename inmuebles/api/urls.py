from rest_framework.routers import DefaultRouter
from .views import InmuebleViewSet

router = DefaultRouter()
router.register('inmuebles', InmuebleViewSet, basename='inmueble')

urlpatterns = router.urls