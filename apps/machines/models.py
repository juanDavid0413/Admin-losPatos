from django.db import models
from django.conf import settings
from django.utils import timezone


class Machine(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Máquina'
        verbose_name_plural = 'Máquinas'

    def __str__(self):
        return self.name


class MachinePayment(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name='payments', verbose_name='Máquina')
    client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='machine_payments', verbose_name='Cliente')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Trabajador')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Pago de Máquina'
        verbose_name_plural = 'Pagos de Máquinas'
        ordering = ['-created_at']

    def __str__(self):
        client_str = f' — {self.client}' if self.client else ''
        return f'{self.machine} ${self.amount}{client_str}'

    def save(self, *args, **kwargs):
        from apps.movements.models import Movement
        from apps.core.constants import MovementType, MovementSource
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new:
            client_str = f' — Cliente: {self.client}' if self.client else ''
            Movement.objects.create(
                movement_type=MovementType.INCOME,
                source=MovementSource.MACHINE,
                amount=self.amount,
                description=f'Pago máquina: {self.machine.name}{client_str}',
                machine=self.machine,
                worker=self.worker,
            )
