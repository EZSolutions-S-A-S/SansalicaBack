from rest_framework import permissions


class IsStaffUser(permissions.BasePermission):
    """Acceso exclusivo para usuarios staff autenticados (panel admin vía JWT)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
