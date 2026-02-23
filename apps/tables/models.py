from django.db import models
from apps.core.constants import TableStatus
from decimal import Decimal


class Table(models.Model):
    """
    Mesa de billar.
    Reglas del documento:
    - Una mesa = una sesión activa máximo
    - Estado se DERIVA de la sesión activa (no manual)
    """
    name = models.CharField(max_length=50, unique=True, verbose_name='Nombre')
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Tarifa por hora'
    )
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def status(self):
        """
        El estado se DERIVA de si hay una sesión activa.
        Nunca se guarda en base de datos — siempre se calcula.
        """
        if self.sessions.filter(closed_at__isnull=True).exists():
            return TableStatus.OCCUPIED
        return TableStatus.FREE

    @property
    def is_free(self):
        return self.status == TableStatus.FREE

    @property
    def minute_rate(self):
        """Valor por minuto = valor_hora / 60 (regla del documento)."""
        return Decimal(self.hourly_rate) / Decimal(60)

    @property
    def active_session(self):
        return self.sessions.filter(closed_at__isnull=True).first()
