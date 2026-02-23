from django.db import models
from django.conf import settings
from apps.core.constants import MovementType, MovementSource


class Movement(models.Model):
    """
    Auditoría de todos los movimientos económicos.
    Reglas del documento:
    - Esta app NO hace lógica, solo registra.
    - Inmutable (no se edita).
    - Toda acción económica = movimiento.
    """
    movement_type = models.CharField(
        max_length=10,
        choices=MovementType.CHOICES,
        verbose_name='Tipo'
    )
    source = models.CharField(
        max_length=20,
        choices=MovementSource.CHOICES,
        verbose_name='Origen'
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Monto'
    )
    description = models.TextField(verbose_name='Descripción')

    # Relaciones opcionales según el origen
    table_session = models.ForeignKey(
        'table_sessions.TableSession',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='movements',
        verbose_name='Sesión de mesa'
    )
    product_account = models.ForeignKey(
        'product_accounts.ProductAccount',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='movements',
        verbose_name='Cuenta de productos'
    )
    machine = models.ForeignKey(
        'machines.Machine',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='movements',
        verbose_name='Máquina'
    )

    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='movements',
        verbose_name='Trabajador'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        ordering = ['-created_at']
        # INMUTABLE: no se pueden editar ni borrar desde admin
        # Se controla a nivel de permisos

    def __str__(self):
        return f'{self.get_movement_type_display()} ${self.amount} — {self.created_at.strftime("%d/%m/%Y %H:%M")}'

    def save(self, *args, **kwargs):
        """Los movimientos NO se editan una vez creados."""
        if self.pk:
            raise ValueError('Los movimientos son inmutables y no se pueden editar.')
        super().save(*args, **kwargs)
