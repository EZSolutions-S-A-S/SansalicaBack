from django.conf import settings
from rest_framework import authentication


class ReadOnlyApiKeyAuthentication(authentication.BaseAuthentication):
    """Autentica requests que envían 'Authorization: Api-Key <token>'.

    No crea ni requiere un usuario: solo marca el request como autenticado
    por API key para que ReadOnlyOrAdmin permita el acceso de lectura.
    """

    keyword = 'Api-Key'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode('utf-8')
        if not header or not header.startswith(f'{self.keyword} '):
            return None

        token = header[len(self.keyword) + 1:].strip()
        if not settings.READ_API_KEY or token != settings.READ_API_KEY:
            return None

        return (None, token)
