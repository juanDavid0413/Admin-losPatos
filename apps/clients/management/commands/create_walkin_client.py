"""
Crea el cliente especial 'Cliente de Paso' si no existe.
Correr una sola vez: python manage.py create_walkin_client
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea el cliente especial Cliente de Paso'

    def handle(self, *args, **kwargs):
        from apps.clients.models import Client
        client, created = Client.objects.get_or_create(
            name='Cliente de Paso',
            defaults={
                'phone': '',
                'notes': 'Cliente especial para visitas esporadicas. Usar alias en cada sesion.',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Cliente de Paso creado con ID={client.pk}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Cliente de Paso ya existe (ID={client.pk})'
            ))
