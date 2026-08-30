from rest_framework import permissions


class HasApiKey(permissions.BasePermission):
    """Acceso de solo lectura al catálogo público — requiere una API Key válida.

    Las operaciones de escritura no existen en este endpoint: viven en el
    namespace admin (ver inmuebles/api/admin/permissions.py::IsStaffUser),
    protegidas por JWT.
    """

    def has_permission(self, request, view):
        return bool(request.successful_authenticator)
