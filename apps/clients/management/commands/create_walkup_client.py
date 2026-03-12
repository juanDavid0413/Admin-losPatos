"""
Crea el cliente especial 'Cliente de Paso' en la base de datos.
Ejecutar una sola vez: python manage.py create_walkup_client
"""
from django.core.management.base import BaseCommand
from apps.clients.models import Client


class Command(BaseCommand):
    help = 'Crea el cliente especial de paso'

    def handle(self, *args, **kwargs):
        client, created = Client.objects.get_or_create(
            name='Cliente de Paso',
            defaults={
                'phone': '',
                'notes': 'Cliente especial para personas ocasionales. El alias se guarda en las notas de cada sesion.',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Cliente de paso creado (id={client.pk})'))
        else:
            self.stdout.write(self.style.WARNING(f'Ya existe (id={client.pk})'))
