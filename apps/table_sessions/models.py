from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class TableSession(models.Model):

    TIMER_RUNNING = 'running'
    TIMER_PAUSED = 'paused'
    TIMER_STOPPED = 'stopped'   # tiempo detenido, sesion aun abierta
    TIMER_CHOICES = [
        (TIMER_RUNNING, 'Corriendo'),
        (TIMER_PAUSED, 'Pausado'),
        (TIMER_STOPPED, 'Tiempo detenido'),
    ]

    table = models.ForeignKey('tables.Table', on_delete=models.PROTECT, related_name='sessions', verbose_name='Mesa')
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='sessions', verbose_name='Cliente')
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sessions', verbose_name='Trabajador')
    opened_at = models.DateTimeField(default=timezone.now, verbose_name='Inicio')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Cierre')

    # Control del cronometro
    timer_status = models.CharField(max_length=10, choices=TIMER_CHOICES, default=TIMER_RUNNING, verbose_name='Estado cronometro')
    paused_at = models.DateTimeField(null=True, blank=True, verbose_name='Pausado en')
    total_paused_seconds = models.PositiveIntegerField(default=0, verbose_name='Segundos pausados acumulados')
    time_stopped_at = models.DateTimeField(null=True, blank=True, verbose_name='Tiempo detenido en')

    # Totales al cerrar
    time_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'), verbose_name='Total tiempo')
    products_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'), verbose_name='Total productos')
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'), verbose_name='Total general')
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Sesion de Mesa'
        verbose_name_plural = 'Sesiones de Mesa'
        ordering = ['-opened_at']

    def __str__(self):
        status = 'Abierta' if self.is_open else 'Cerrada'
        return f'{self.table} — {self.client} ({status})'

    @property
    def is_open(self):
        return self.closed_at is None

    @property
    def is_timer_running(self):
        return self.timer_status == self.TIMER_RUNNING

    @property
    def is_timer_paused(self):
        return self.timer_status == self.TIMER_PAUSED

    @property
    def is_timer_stopped(self):
        return self.timer_status == self.TIMER_STOPPED

    @property
    def effective_seconds(self):
        """
        Segundos reales de juego = elapsed total - segundos pausados.
        Usado para calcular el costo de tiempo.
        """
        if self.is_timer_stopped and self.time_stopped_at:
            end = self.time_stopped_at
        elif self.closed_at:
            end = self.closed_at
        else:
            end = timezone.now()

        total_elapsed = (end - self.opened_at).total_seconds()

        paused = self.total_paused_seconds
        # Si esta pausado ahora, sumar el tramo actual de pausa
        if self.is_timer_paused and self.paused_at:
            paused += (timezone.now() - self.paused_at).total_seconds()

        return max(0, total_elapsed - paused)

    @property
    def elapsed_minutes(self):
        if self.closed_at:
            end = self.closed_at
            total = (end - self.opened_at).total_seconds()
            return Decimal(max(0, total - self.total_paused_seconds)) / Decimal(60)
        return Decimal(self.effective_seconds) / Decimal(60)

    def calculate_time_cost(self):
        """Redondeado al entero mas cercano — sin centavos."""
        raw = self.table.minute_rate * self.elapsed_minutes
        return raw.quantize(Decimal('1'), rounding='ROUND_HALF_UP')

    def calculate_products_cost(self):
        return sum(item.subtotal for item in self.session_products.all())

    def pause_timer(self):
        if not self.is_timer_running:
            raise ValueError('El cronometro no esta corriendo.')
        self.timer_status = self.TIMER_PAUSED
        self.paused_at = timezone.now()
        self.save(update_fields=['timer_status', 'paused_at'])

    def resume_timer(self):
        if not self.is_timer_paused:
            raise ValueError('El cronometro no esta pausado.')
        if self.paused_at:
            paused_secs = int((timezone.now() - self.paused_at).total_seconds())
            self.total_paused_seconds += paused_secs
        self.timer_status = self.TIMER_RUNNING
        self.paused_at = None
        self.save(update_fields=['timer_status', 'paused_at', 'total_paused_seconds'])

    def stop_timer(self):
        """Detiene el cobro del tiempo pero deja la sesion abierta para agregar productos."""
        if self.is_timer_stopped:
            raise ValueError('El tiempo ya esta detenido.')
        # Si estaba pausado, cerrar esa pausa primero
        if self.is_timer_paused and self.paused_at:
            paused_secs = int((timezone.now() - self.paused_at).total_seconds())
            self.total_paused_seconds += paused_secs
            self.paused_at = None
        self.timer_status = self.TIMER_STOPPED
        self.time_stopped_at = timezone.now()
        self.save(update_fields=['timer_status', 'paused_at', 'total_paused_seconds', 'time_stopped_at'])

    def close(self, worker, paid=True):
        from apps.movements.models import Movement
        from apps.core.constants import MovementType, MovementSource
        from apps.receivables.models import Receivable

        if not self.is_open:
            raise ValueError('Esta sesion ya esta cerrada.')

        # Si estaba pausado al cerrar, cerrar la pausa
        if self.is_timer_paused and self.paused_at:
            paused_secs = int((timezone.now() - self.paused_at).total_seconds())
            self.total_paused_seconds += paused_secs
            self.paused_at = None

        self.closed_at = timezone.now()
        self.time_total = self.calculate_time_cost()
        products = Decimal(str(self.calculate_products_cost()))
        self.products_total = products.quantize(Decimal('1'), rounding='ROUND_HALF_UP')
        self.grand_total = self.time_total + self.products_total
        self.save()

        if paid:
            Movement.objects.create(
                movement_type=MovementType.INCOME,
                source=MovementSource.TABLE_SESSION,
                amount=self.grand_total,
                description=f'Cierre sesion {self.table.name} — {self.client.name} — {self.elapsed_minutes:.0f} min efectivos',
                table_session=self,
                worker=worker,
            )
        else:
            Receivable.objects.create(
                source=Receivable.SOURCE_SESSION,
                table_session=self,
                client=self.client,
                amount=self.grand_total,
                notes=f'Sesion mesa {self.table.name} — {self.elapsed_minutes:.0f} min efectivos',
            )


class SessionProduct(models.Model):
    session = models.ForeignKey(TableSession, on_delete=models.CASCADE, related_name='session_products', verbose_name='Sesion')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, verbose_name='Producto')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Cantidad')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')

    class Meta:
        verbose_name = 'Producto en Sesion'
        verbose_name_plural = 'Productos en Sesion'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        if not self.pk:
            self.product.discount_stock(self.quantity)
            if not self.unit_price:
                self.unit_price = self.product.sale_price
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.product.restore_stock(self.quantity)
        super().delete(*args, **kwargs)
