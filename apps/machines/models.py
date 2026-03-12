from django.db import models
from django.conf import settings
from django.utils import timezone


class Machine(models.Model):
    name        = models.CharField(max_length=100, verbose_name='Nombre')
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Maquina'
        verbose_name_plural = 'Maquinas'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_paid(self):
        from django.db.models import Sum
        return self.payments.aggregate(t=Sum('amount'))['t'] or 0


class MachinePayment(models.Model):
    machine    = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name='payments')
    worker     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='machine_payments')
    # client es OPCIONAL - puede no tener cliente asociado
    client     = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='machine_payments')
    amount     = models.DecimalField(max_digits=10, decimal_places=2)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Pago de Maquina'
        verbose_name_plural = 'Pagos de Maquinas'
        ordering = ['-created_at']

    def __str__(self):
        c = f' — {self.client.name}' if self.client else ''
        return f'{self.machine.name}{c}: ${self.amount}'
