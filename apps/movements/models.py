from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.constants import MovementType, MovementSource


class Movement(models.Model):
    movement_type = models.CharField(
        max_length=10, choices=MovementType.CHOICES, verbose_name='Tipo'
    )
    source = models.CharField(
        max_length=20, choices=MovementSource.CHOICES, verbose_name='Origen'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto')
    description = models.TextField(verbose_name='Descripcion')

    # Relaciones opcionales al origen
    table_session = models.ForeignKey(
        'table_sessions.TableSession', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='movements', verbose_name='Sesion de mesa'
    )
    product_account = models.ForeignKey(
        'product_accounts.ProductAccount', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='movements', verbose_name='Cuenta de productos'
    )
    machine_payment = models.ForeignKey(
        'machines.MachinePayment', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='movements', verbose_name='Pago de maquina'
    )

    # Cliente asociado (desnormalizado para acceso rapido)
    client = models.ForeignKey(
        'clients.Client', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='movements', verbose_name='Cliente'
    )

    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='movements', verbose_name='Trabajador'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_movement_type_display()} ${self.amount} — {self.created_at:%d/%m/%Y}'
