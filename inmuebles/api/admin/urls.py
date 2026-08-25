from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import AdminInmuebleViewSet

router = DefaultRouter()
router.register('inmuebles', AdminInmuebleViewSet, basename='admin-inmueble')

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='admin-token-obtain-pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='admin-token-refresh'),
] + router.urls
