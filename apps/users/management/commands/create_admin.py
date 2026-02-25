"""
Comando para crear superusuario desde variables de entorno.
Uso: python manage.py create_admin
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Crea el superusuario admin desde variables de entorno'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@billar.com')
        password = os.environ.get('ADMIN_PASSWORD', '')

        if not password:
            self.stdout.write(self.style.ERROR(
                'Define la variable ADMIN_PASSWORD en Railway antes de correr este comando.'
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'El usuario "{username}" ya existe.'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente.'))