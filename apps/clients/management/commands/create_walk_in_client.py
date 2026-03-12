"""
Crea el cliente especial 'Cliente de Paso' si no existe.
Correr una vez: python manage.py create_walk_in_client
"""
from django.core.management.base import BaseCommand
from apps.clients.models import Client


WALK_IN_NAME = 'Cliente de Paso'


def get_or_create_walk_in():
    client, created = Client.objects.get_or_create(
        name=WALK_IN_NAME,
        defaults={
            'phone': '',
            'notes': 'Cliente generico para visitantes ocasionales. No eliminar.',
            'is_active': True,
        }
    )
    return client, created


class Command(BaseCommand):
    help = 'Crea el cliente especial "Cliente de Paso"'

    def handle(self, *args, **kwargs):
        client, created = get_or_create_walk_in()
        if created:
            self.stdout.write(self.style.SUCCESS(f'Cliente de Paso creado (id={client.pk})'))
        else:
            self.stdout.write(self.style.WARNING(f'Ya existe (id={client.pk})'))
