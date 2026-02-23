from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class ProductAccount(models.Model):
    """
    Cuentas solo de productos — sin mesa, sin tiempo.
    Regla del documento: 'Nunca mezclar con sesiones de mesa.'
    Pueden permanecer abiertas.
    """
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='product_accounts',
        verbose_name='Cliente'
    )
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='product_accounts',
        verbose_name='Trabajador'
    )
    opened_at = models.DateTimeField(default=timezone.now, verbose_name='Apertura')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Cierre')
    grand_total = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0'),
        verbose_name='Total'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        verbose_name = 'Cuenta de Productos'
        verbose_name_plural = 'Cuentas de Productos'
        ordering = ['-opened_at']

    def __str__(self):
        status = 'Abierta' if self.is_open else 'Cerrada'
        return f'Cuenta {self.client} ({status})'

    @property
    def is_open(self):
        return self.closed_at is None

    def calculate_total(self):
        return sum(
            item.unit_price * item.quantity
            for item in self.account_products.all()
        )

    def close(self, worker=None):
        from apps.movements.models import Movement
        from apps.core.constants import MovementType, MovementSource

        if not self.is_open:
            raise ValueError('Esta cuenta ya está cerrada.')

        self.closed_at = timezone.now()
        self.grand_total = Decimal(self.calculate_total())
        self.save()

        Movement.objects.create(
            movement_type=MovementType.INCOME,
            source=MovementSource.PRODUCT_ACCOUNT,
            amount=self.grand_total,
            description=f'Cierre cuenta productos — Cliente: {self.client.name}',
            product_account=self,
            worker=worker or self.worker,
        )


class AccountProduct(models.Model):
    """Producto dentro de una cuenta de productos."""
    account = models.ForeignKey(
        ProductAccount,
        on_delete=models.CASCADE,
        related_name='account_products',
        verbose_name='Cuenta'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        verbose_name='Producto'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='Cantidad')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')

    class Meta:
        verbose_name = 'Producto en Cuenta'
        verbose_name_plural = 'Productos en Cuenta'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.product.discount_stock(self.quantity)
            if not self.unit_price:
                self.unit_price = self.product.sale_price
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.product.restore_stock(self.quantity)
        super().delete(*args, **kwargs)
