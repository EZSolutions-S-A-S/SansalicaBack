from rest_framework import permissions


class ReadOnlyOrAdmin(permissions.BasePermission):
    """Lectura (GET/HEAD/OPTIONS): requiere API Key válida.

    Escritura (POST/PUT/PATCH/DELETE): requiere un usuario staff con
    sesión iniciada (uso exclusivo desde Django Admin).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.successful_authenticator)

        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
