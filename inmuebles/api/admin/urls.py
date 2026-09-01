from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView

from .views import AdminInmuebleViewSet, AdminProfileView, ChangePasswordView

router = DefaultRouter()
router.register('inmuebles', AdminInmuebleViewSet, basename='admin-inmueble')

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='admin-token-obtain-pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='admin-token-refresh'),
    path('auth/logout/', TokenBlacklistView.as_view(), name='admin-token-blacklist'),
    path('me/', AdminProfileView.as_view(), name='admin-profile'),
    path('me/change-password/', ChangePasswordView.as_view(), name='admin-change-password'),
] + router.urls
