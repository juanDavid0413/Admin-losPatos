from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class TableSession(models.Model):
    table = models.ForeignKey('tables.Table', on_delete=models.PROTECT, related_name='sessions', verbose_name='Mesa')
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='sessions', verbose_name='Cliente')
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sessions', verbose_name='Trabajador')
    opened_at = models.DateTimeField(default=timezone.now, verbose_name='Inicio')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Cierre')
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
    def elapsed_minutes(self):
        end = self.closed_at or timezone.now()
        delta = end - self.opened_at
        return Decimal(delta.total_seconds()) / Decimal(60)

    def calculate_time_cost(self):
        return (self.table.minute_rate * self.elapsed_minutes).quantize(Decimal('0.01'))

    def calculate_products_cost(self):
        return sum(item.subtotal for item in self.session_products.all())

    def close(self, worker, paid=True):
        from apps.movements.models import Movement
        from apps.core.constants import MovementType, MovementSource
        from apps.receivables.models import Receivable

        if not self.is_open:
            raise ValueError('Esta sesion ya esta cerrada.')

        self.closed_at = timezone.now()
        self.time_total = self.calculate_time_cost()
        self.products_total = Decimal(str(self.calculate_products_cost()))
        self.grand_total = self.time_total + self.products_total
        self.save()

        if paid:
            Movement.objects.create(
                movement_type=MovementType.INCOME,
                source=MovementSource.TABLE_SESSION,
                amount=self.grand_total,
                description=f'Cierre sesion {self.table.name} — {self.client.name} — {self.elapsed_minutes:.0f} min',
                table_session=self,
                worker=worker,
            )
        else:
            Receivable.objects.create(
                source=Receivable.SOURCE_SESSION,
                table_session=self,
                client=self.client,
                amount=self.grand_total,
                notes=f'Sesion mesa {self.table.name} — {self.elapsed_minutes:.0f} min',
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
