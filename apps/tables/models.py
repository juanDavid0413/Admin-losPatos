from django.db import models
from apps.core.constants import TableStatus
from decimal import Decimal


class Table(models.Model):

    TYPE_TRES_BANDAS = 'tres_bandas'
    TYPE_LIBRE       = 'libre'
    TYPE_POOL        = 'pool'
    TYPE_CHOICES = [
        (TYPE_TRES_BANDAS, '3 Bandas'),
        (TYPE_LIBRE,       'Libre'),
        (TYPE_POOL,        'Pool'),
    ]

    # Imagen de fondo por tipo (en static/img/tables/)
    TYPE_IMAGES = {
        TYPE_TRES_BANDAS: 'img/tables/tres_bandas.jpg',
        TYPE_LIBRE:       'img/tables/libre.jpg',
        TYPE_POOL:        'img/tables/pool.jpg',
    }

    name        = models.CharField(max_length=50, unique=True, verbose_name='Nombre')
    table_type  = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default=TYPE_LIBRE,
        verbose_name='Tipo de mesa'
    )
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Tarifa por hora'
    )
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_active   = models.BooleanField(default=True, verbose_name='Activa')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def bg_image(self):
        """Ruta relativa a static/ para usar en templates con {% static %}."""
        return self.TYPE_IMAGES.get(self.table_type, '')

    @property
    def status(self):
        if self.sessions.filter(closed_at__isnull=True).exists():
            return TableStatus.OCCUPIED
        return TableStatus.FREE

    @property
    def is_free(self):
        return self.status == TableStatus.FREE

    @property
    def minute_rate(self):
        return Decimal(self.hourly_rate) / Decimal(60)

    @property
    def active_session(self):
        return self.sessions.filter(closed_at__isnull=True).first()
