import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Crea el superusuario staff inicial desde variables de entorno, sin
    necesitar Shell (no disponible en el plan gratis de Render). Seguro de
    correr en cada deploy: si el usuario ya existe, no hace nada."""

    help = 'Crea el superusuario inicial desde DJANGO_SUPERUSER_USERNAME/PASSWORD/EMAIL, si no existe todavía.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write('DJANGO_SUPERUSER_USERNAME/PASSWORD no configurados, se omite.')
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'El usuario "{username}" ya existe, se omite.')
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(f'Superusuario "{username}" creado.')
