from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class ProductAccount(models.Model):
    client       = models.ForeignKey('clients.Client', on_delete=models.PROTECT, related_name='product_accounts')
    worker       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='product_accounts')
    client_alias = models.CharField(max_length=100, blank=True, verbose_name='Nombre de paso')
    opened_at    = models.DateTimeField(default=timezone.now)
    closed_at    = models.DateTimeField(null=True, blank=True)
    grand_total  = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    notes        = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Cuenta de Productos'
        verbose_name_plural = 'Cuentas de Productos'
        ordering = ['-opened_at']

    def __str__(self):
        return f'Cuenta {self.display_name}'

    @property
    def display_name(self):
        if self.client_alias:
            return f'Cliente de Paso ({self.client_alias})'
        return self.client.name

    @property
    def is_open(self):
        return self.closed_at is None

    def calculate_total(self):
        return sum(item.unit_price * item.quantity for item in self.account_products.all())

    def close(self, worker, paid=True):
        from apps.movements.models import Movement
        from apps.core.constants import MovementType, MovementSource
        from apps.receivables.models import Receivable

        if not self.is_open:
            raise ValueError('Esta cuenta ya esta cerrada.')

        self.closed_at = timezone.now()
        total = Decimal(str(self.calculate_total()))
        self.grand_total = total.quantize(Decimal('1'), rounding='ROUND_HALF_UP')
        self.save()

        desc = f'Cierre cuenta productos — {self.display_name}'

        if paid:
            Movement.objects.create(
                movement_type=MovementType.INCOME,
                source=MovementSource.PRODUCT_ACCOUNT,
                amount=self.grand_total,
                description=desc,
                product_account=self,
                client=self.client,
                worker=worker,
            )
        else:
            Receivable.objects.create(
                source=Receivable.SOURCE_ACCOUNT,
                product_account=self,
                client=self.client,
                amount=self.grand_total,
                notes=desc,
            )


class AccountProduct(models.Model):
    account    = models.ForeignKey(ProductAccount, on_delete=models.CASCADE, related_name='account_products')
    product    = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity   = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.product.discount_stock(self.quantity)
            if not self.unit_price:
                self.unit_price = self.product.sale_price
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.product.restore_stock(self.quantity)
        super().delete(*args, **kwargs)
